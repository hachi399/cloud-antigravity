// Firebase CDN インポート (v10 modular)
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
import { 
  getAuth, 
  signInWithPopup, 
  GoogleAuthProvider, 
  onAuthStateChanged, 
  signOut 
} from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";

// ==========================================
// 設定情報（※自身の GCP / Firebase の値に差し替え）
// ==========================================
const CONFIG = {
  // Cloud Run デプロイ後のエンドポイント URL
  apiBaseUrl: window.API_BASE_URL || "https://cloud-antigravity-api-xxxx.a.run.app",
  
  // 認可する正規 Google メールアドレス（ホワイトリスト）
  allowedEmail: "yonghachi399@gmail.com",

  // Firebase Web アプリ設定（Firebase Console から取得）
  firebaseConfig: {
    apiKey: "YOUR_FIREBASE_API_KEY",
    authDomain: "YOUR_PROJECT_ID.firebaseapp.com",
    projectId: "YOUR_PROJECT_ID",
    storageBucket: "YOUR_PROJECT_ID.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
  }
};

// Firebase 初期化
const app = initializeApp(CONFIG.firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

// DOM 要素
const loginSection = document.getElementById("login-section");
const appSection = document.getElementById("app-section");
const loginBtn = document.getElementById("login-btn");
const logoutBtn = document.getElementById("logout-btn");
const userDisplay = document.getElementById("user-display");
const authIndicator = document.querySelector(".status-indicator");
const taskForm = document.getElementById("task-form");
const submitBtn = document.getElementById("submit-btn");
const statusCard = document.getElementById("status-card");
const taskBadge = document.getElementById("task-badge");
const taskIdDisplay = document.getElementById("task-id-display");
const taskSummary = document.getElementById("task-summary");
const progressBar = document.getElementById("progress-bar");
const inboxList = document.getElementById("inbox-list");
const refreshInboxBtn = document.getElementById("refresh-inbox-btn");

let currentUser = null;
let currentTaskId = null;
let pollTimer = null;

// ==========================================
// 認証ロジック
// ==========================================
onAuthStateChanged(auth, async (user) => {
  if (user) {
    const email = user.email.toLowerCase();
    // クライアント側でも一次検証
    if (email !== CONFIG.allowedEmail.toLowerCase()) {
      alert(`アクセス拒否: このアカウント (${email}) は登録されていません。`);
      await signOut(auth);
      return;
    }

    currentUser = user;
    userDisplay.textContent = user.displayName || user.email;
    authIndicator.classList.remove("offline");
    authIndicator.classList.add("online");

    loginSection.classList.add("hidden");
    appSection.classList.remove("hidden");

    // inbox の読み込み
    fetchInbox();
  } else {
    currentUser = null;
    userDisplay.textContent = "未認証";
    authIndicator.classList.remove("online");
    authIndicator.classList.add("offline");

    loginSection.classList.remove("hidden");
    appSection.classList.add("hidden");
  }
});

loginBtn.addEventListener("click", async () => {
  try {
    await signInWithPopup(auth, provider);
  } catch (error) {
    console.error("ログインエラー:", error);
    alert(`ログインに失敗しました: ${error.message}`);
  }
});

logoutBtn.addEventListener("click", async () => {
  if (pollTimer) clearInterval(pollTimer);
  await signOut(auth);
});

// ==========================================
// API 呼び出しヘルパー (認証ヘッダー付与)
// ==========================================
async function authenticatedFetch(path, options = {}) {
  if (!currentUser) throw new Error("未ログインです。");

  // 有効な ID トークン（JWT）を常に最新で取得
  const token = await currentUser.getIdToken(true);

  const headers = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${token}`,
    ...(options.headers || {})
  };

  const response = await fetch(`${CONFIG.apiBaseUrl}${path}`, {
    ...options,
    headers
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(errorData.detail || "API 通信エラー");
  }

  return response.json();
}

// ==========================================
// PC 投函コンテキスト (Inbox) 取得
// ==========================================
async function fetchInbox() {
  try {
    inboxList.innerHTML = `<span class="text-muted">確認中...</span>`;
    const files = await authenticatedFetch("/api/v1/inbox");
    if (!files || files.length === 0) {
      inboxList.innerHTML = `<span class="text-muted">投函されたファイルはありません（空）</span>`;
      return;
    }
    inboxList.innerHTML = files.map(file => `<span class="inbox-tag">📄 ${file}</span>`).join("");
  } catch (err) {
    inboxList.innerHTML = `<span class="text-muted">取得スキップ (${err.message})</span>`;
  }
}

refreshInboxBtn.addEventListener("click", fetchInbox);

// ==========================================
// タスク送信 & 進捗ポーリング
// ==========================================
taskForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const prompt = document.getElementById("prompt").value.trim();
  const taskType = document.getElementById("task-type").value;

  if (!prompt) return;

  submitBtn.disabled = true;
  submitBtn.textContent = "送信中...";

  try {
    const res = await authenticatedFetch("/api/v1/tasks", {
      method: "POST",
      body: JSON.stringify({ prompt, task_type: taskType })
    });

    currentTaskId = res.task_id;
    showStatusCard(currentTaskId, "pending", "タスクを受理しました。待機中...");

    // 入力欄をクリア
    document.getElementById("prompt").value = "";

    // ポーリング開始（3秒間隔）
    startStatusPolling(currentTaskId);
  } catch (err) {
    alert(`タスク送信失敗: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "エージェントへ発令";
  }
});

function showStatusCard(taskId, status, summary) {
  statusCard.classList.remove("hidden");
  taskIdDisplay.textContent = `ID: ${taskId}`;
  updateBadge(status);
  taskSummary.textContent = summary;
}

function updateBadge(status) {
  taskBadge.className = `badge ${status}`;
  if (status === "pending") {
    taskBadge.textContent = "待機中";
    progressBar.className = "progress-bar";
    progressBar.style.width = "20%";
  } else if (status === "running") {
    taskBadge.textContent = "実行中";
    progressBar.className = "progress-bar animated";
  } else if (status === "completed") {
    taskBadge.textContent = "完了";
    progressBar.className = "progress-bar";
    progressBar.style.width = "100%";
  } else if (status === "failed") {
    taskBadge.textContent = "エラー";
    progressBar.className = "progress-bar";
    progressBar.style.backgroundColor = "var(--danger)";
    progressBar.style.width = "100%";
  }
}

function startStatusPolling(taskId) {
  if (pollTimer) clearInterval(pollTimer);

  pollTimer = setInterval(async () => {
    try {
      const res = await authenticatedFetch(`/api/v1/tasks/${taskId}/status`);
      updateBadge(res.status);
      taskSummary.textContent = res.summary || "";

      if (res.status === "completed" || res.status === "failed") {
        clearInterval(pollTimer);
        pollTimer = null;
      }
    } catch (err) {
      console.warn("ステータス取得失敗:", err);
    }
  }, 3000);
}
