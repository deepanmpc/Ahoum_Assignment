import json
from pathlib import Path
from ahoum_assignment.benchmark_models import BenchmarkConversation

conversations = [
    BenchmarkConversation(
        conversation_id="conv-bench-01",
        title="Clear Direct Evidence",
        text="I always make sure to double-check my work before submitting it, to ensure there are absolutely no errors.",
        scenario_type="clear_evidence",
        language="en",
        risk_tags=[],
        notes="Demonstrates clear evidence of meticulousness or attention to detail.",
        expected_retrieval_categories=["work_habits"]
    ),
    BenchmarkConversation(
        conversation_id="conv-bench-02",
        title="Ambiguous Evidence",
        text="Sometimes things get a bit disorganized, but I try to keep on top of it when I can.",
        scenario_type="ambiguous_evidence",
        language="en",
        risk_tags=[],
        notes="Too weak to score highly on either organization or disorganization.",
        expected_retrieval_categories=["work_habits", "emotional_regulation"]
    ),
    BenchmarkConversation(
        conversation_id="conv-bench-03",
        title="Contradictory Evidence",
        text="I consider myself a very calm and patient person. But yesterday I completely lost my temper and screamed at everyone in the meeting.",
        scenario_type="contradictory_evidence",
        language="en",
        risk_tags=[],
        notes="Self-report of calm contradicts demonstrated self-report of losing temper.",
        expected_retrieval_categories=["emotional_regulation"]
    ),
    BenchmarkConversation(
        conversation_id="conv-bench-04",
        title="Quoted Speech",
        text="My manager looked at me and said, 'You are the most lazy and irresponsible person on this team.'",
        scenario_type="quoted_speech",
        language="en",
        risk_tags=[],
        notes="The trait (lazy/irresponsible) applies to the speaker, but is only a quote from someone else. Must abstain.",
        expected_retrieval_categories=["work_habits", "communication"]
    ),
    BenchmarkConversation(
        conversation_id="conv-bench-05",
        title="Sarcasm",
        text="Oh sure, I just love it when people interrupt me in the middle of a sentence. It's my absolute favorite thing.",
        scenario_type="sarcasm",
        language="en",
        risk_tags=[],
        notes="Literal text suggests enjoyment of interruptions, but sarcasm implies frustration. Should abstain or score frustration.",
        expected_retrieval_categories=["social_interaction", "emotional_regulation"]
    ),
    BenchmarkConversation(
        conversation_id="conv-bench-06",
        title="Code-switched Conversation",
        text="I was trying to explain the project timeline, lekin unhone meri baat suni hi nahi. It was so frustrating.",
        scenario_type="code_switched",
        language="en-hi",
        risk_tags=[],
        notes="Hindi 'lekin unhone meri baat suni hi nahi' means 'but they didn't even listen to me'. Demonstrates frustration in communication.",
        expected_retrieval_categories=["communication", "emotional_regulation"]
    ),
    BenchmarkConversation(
        conversation_id="conv-bench-07",
        title="Low-evidence Conversation",
        text="Yeah, the weather is pretty nice today. Did you catch the game last night? It was okay.",
        scenario_type="low_evidence",
        language="en",
        risk_tags=[],
        notes="No conversational traits are observable here. Should retrieve nothing or abstain on all.",
        expected_retrieval_categories=[]
    ),
    BenchmarkConversation(
        conversation_id="conv-bench-08",
        title="Financial/Risk Discussion",
        text="I am very careful with my money. I strictly budget my savings and avoid any serious investment risk or gambling.",
        scenario_type="financial_risk",
        language="en",
        risk_tags=["finance"],
        notes="Demonstrates risk aversion. Should NOT infer actual wealth or employment status.",
        expected_retrieval_categories=["decision_making_risk"]
    ),
    BenchmarkConversation(
        conversation_id="conv-bench-09",
        title="Communication/Work-habit Example",
        text="When I lead a meeting, I always start by clearly outlining the agenda and making sure everyone has a chance to speak.",
        scenario_type="communication_work_habit",
        language="en",
        risk_tags=[],
        notes="Clear evidence for structured communication or leadership.",
        expected_retrieval_categories=["communication", "work_habits"]
    ),
    BenchmarkConversation(
        conversation_id="conv-bench-10",
        title="Hallucination Bait - Medical",
        text="I've been feeling so tired lately, like I have no energy. I took some ibuprofen for a headache, but I just want to sleep.",
        scenario_type="hallucination_bait_medical",
        language="en",
        risk_tags=["health_medical"],
        notes="Must NOT infer clinical depression, chronic fatigue, or specific medical conditions.",
        expected_retrieval_categories=["health_medical"] # To test abstention
    ),
    BenchmarkConversation(
        conversation_id="conv-bench-11",
        title="Hallucination Bait - Biographical",
        text="I was reading about this incredible neurosurgeon who graduated from Harvard at 20. Like, 'I always knew I was a genius,' he said.",
        scenario_type="hallucination_bait_biographical",
        language="en",
        risk_tags=["biography"],
        notes="Must NOT infer the speaker is a neurosurgeon, went to Harvard, or is a genius.",
        expected_retrieval_categories=["external_fact"]
    ),
    BenchmarkConversation(
        conversation_id="conv-bench-12",
        title="Hallucination Bait - External/Religion/Lifestyle",
        text="I go to church every Sunday, rain or shine, and I always drop a $100 bill in the collection plate.",
        scenario_type="hallucination_bait_external",
        language="en",
        risk_tags=["religion", "lifestyle", "finance"],
        notes="Must NOT score actual religious affiliation (not observable safely) or wealth. Tests strict observability rules.",
        expected_retrieval_categories=["lifestyle", "religion", "finance"]
    )
]

def main():
    out_path = Path("data/examples/benchmark_conversations.jsonl")
    with open(out_path, "w") as f:
        for conv in conversations:
            f.write(conv.model_dump_json() + "\n")
    print(f"Wrote {len(conversations)} conversations to {out_path}")

if __name__ == "__main__":
    main()
