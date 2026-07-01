"""Gradio app for AgentBridge."""

from __future__ import annotations

import uuid

import gradio as gr

from agentbridge.graph.helpers import format_graph_result, format_interrupt_payload
from agentbridge.graph.runtime import flush_langsmith_traces, get_pending_interrupt, resume_recommendation, run_recommendation


def gradio_respond(user_input: str, history, thread_id: str | None, pending_interrupt):
    user_input = (user_input or "").strip()
    history = history or []
    thread_id = thread_id or f"agentbridge-gradio-{uuid.uuid4().hex}"

    if not user_input:
        return "", history, thread_id, pending_interrupt

    history.append({"role": "user", "content": user_input})

    try:
        if pending_interrupt:
            result = resume_recommendation(user_input, thread_id=thread_id)
        else:
            result = run_recommendation(user_input, thread_id=thread_id)

        pending_interrupt = get_pending_interrupt(result)
        assistant_message = format_interrupt_payload(pending_interrupt) if pending_interrupt else format_graph_result(result)
    except Exception as exc:
        pending_interrupt = None
        assistant_message = f"Error while running graph: {exc}"
    finally:
        flush_langsmith_traces()

    history.append({"role": "assistant", "content": assistant_message})
    return "", history, thread_id, pending_interrupt


def gradio_reset():
    return [], f"agentbridge-gradio-{uuid.uuid4().hex}", None


def create_app() -> gr.Blocks:
    with gr.Blocks() as demo:
        gr.Markdown("## AgentBridge Framework Chooser")
        gr.Markdown(
            "Ask a framework-selection question. If required context is missing, "
            "the graph interrupts and this UI resumes the same LangGraph thread after your answer."
        )

        chatbot = gr.Chatbot()
        user_box = gr.Textbox(
            label="Message",
            placeholder="Ask a framework question, then answer the follow-up if the graph interrupts.",
        )
        with gr.Row():
            send_button = gr.Button("Send", variant="primary")
            clear_button = gr.Button("New conversation")

        thread_state = gr.State(None)
        pending_interrupt_state = gr.State(None)

        user_box.submit(
            gradio_respond,
            inputs=[user_box, chatbot, thread_state, pending_interrupt_state],
            outputs=[user_box, chatbot, thread_state, pending_interrupt_state],
        )
        send_button.click(
            gradio_respond,
            inputs=[user_box, chatbot, thread_state, pending_interrupt_state],
            outputs=[user_box, chatbot, thread_state, pending_interrupt_state],
        )
        clear_button.click(
            gradio_reset,
            outputs=[chatbot, thread_state, pending_interrupt_state],
        )

    return demo


def launch_app() -> None:
    create_app().launch()


def main() -> None:
    launch_app()


if __name__ == "__main__":
    main()
