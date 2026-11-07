"""Antigravity エージェント実行エンジン
"""
import os
import asyncio
from typing import Dict, Any, Tuple
from storage import read_inbox_context, save_task_result, update_task_status

# Antigravity Python SDK のインポート試行
try:
    from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
    ANTIGRAVITY_SDK_AVAILABLE = True
except ImportError:
    ANTIGRAVITY_SDK_AVAILABLE = False

async def run_antigravity_task(task_id: str, prompt: str, task_type: str = "general"):
    """非同期バックグラウンドで Antigravity エージェントを実行し、GCS 専用バケットへ保存する。"""
    try:
        update_task_status(task_id, "running", summary="エージェントがタスクを実行中です...")

        # 1. PC から事前に投函された inbox コンテキストの取得
        inbox_context = read_inbox_context()
        combined_prompt = ""
        if inbox_context:
            combined_prompt += f"【PCから提供された事前コンテキスト】\n{inbox_context}\n\n"
        combined_prompt += f"【指示内容】\n{prompt}\n"

        system_instruction = (
            "お前はクラウド上で常駐稼働する開発支援エージェント『Antigravity』だ。"
            "提供されたコンテキストと指示に基づき、論理的・高精度に設計・コード生成・分析を行え。"
            "生成する成果物は、後で自宅PCから回収・実行されることを意識し、明快なコードと解説を出力しろ。"
        )

        result_text = ""
        files_generated = {}

        if ANTIGRAVITY_SDK_AVAILABLE:
            # 公式 Antigravity Python SDK を使用
            config = LocalAgentConfig(
                system_instructions=system_instruction,
                capabilities=CapabilitiesConfig()
            )
            async with Agent(config) as agent:
                response = await agent.chat(combined_prompt)
                async for token in response:
                    result_text += token
        else:
            # SDK が未準備の環境向けの軽量フォールバック（Gemini API 直接呼び出し）
            import google.generativeai as genai
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-pro", system_instruction=system_instruction)
                resp = model.generate_content(combined_prompt)
                result_text = resp.text
            else:
                result_text = (
                    f"【シミュレーション完了】タスク {task_id} を正常に受領しました。\n"
                    f"プロンプト: {prompt}\n"
                    "（本番稼働時には google-antigravity SDK または GEMINI_API_KEY により本モデルが駆動します）"
                )

        # 成果物の保存
        save_task_result(
            task_id=task_id,
            prompt=prompt,
            result_text=result_text,
            files_generated=files_generated
        )

    except Exception as e:
        update_task_status(task_id, "failed", summary=f"実行中にエラーが発生しました: {str(e)}")
