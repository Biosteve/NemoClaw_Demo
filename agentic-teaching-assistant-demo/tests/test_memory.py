"""
Example: Using Agent Memory in Study Buddy

This example demonstrates how the memory system enhances study buddy conversations.
"""

import asyncio
from agent_memory import get_memory_ops

async def example_conversation():
    """Simulate a conversation with memory"""
    
    # Get memory ops for a user
    username = "example_student"
    memory_ops = get_memory_ops(username)
    
    print("\n" + "="*60)
    print("EXAMPLE STUDY BUDDY CONVERSATION WITH MEMORY")
    print("="*60 + "\n")
    
    # Conversation turns
    conversations = [
        {
            "user": "What is photosynthesis?",
            "bot": "Photosynthesis is the process by which plants use sunlight to convert carbon dioxide and water into glucose and oxygen. It occurs in the chloroplasts of plant cells."
        },
        {
            "user": "How does cellular respiration differ from it?",
            "bot": "Cellular respiration is essentially the reverse of photosynthesis. While photosynthesis stores energy by producing glucose, cellular respiration releases that energy by breaking down glucose. Both processes are complementary in the carbon cycle."
        },
        {
            "user": "Tell me about mitochondria",
            "bot": "Mitochondria are the powerhouse of the cell! They're where cellular respiration happens. They have a double membrane structure and their own DNA, suggesting they were once independent bacteria."
        },
        {
            "user": "What did we discuss about plants earlier?",  # Memory recall triggered!
            "bot": "Earlier, we discussed photosynthesis - the process plants use to convert sunlight, CO2, and water into glucose and oxygen. We also talked about how it contrasts with cellular respiration."
        }
    ]
    
    # Process each conversation turn
    for i, turn in enumerate(conversations, 1):
        user_msg = turn["user"]
        bot_msg = turn["bot"]
        
        print(f"\n{'─'*60}")
        print(f"TURN {i}")
        print(f"{'─'*60}")
        print(f"\n👤 USER: {user_msg}")
        
        # Get memory context before responding
        memory_context = memory_ops.get_memory_context(user_msg)
        history_summary = memory_ops.get_history_summary()
        
        if memory_context:
            print(f"\n🧠 MEMORY RECALLED:")
            print(memory_context)
        
        if history_summary:
            print(f"\n📝 SUMMARY:")
            print(history_summary)
        
        print(f"\n🤖 ASSISTANT: {bot_msg}")
        
        # Process message through memory system
        result = await memory_ops.process_message(
            message=user_msg,
            bot_response=bot_msg,
            context={"chapter": "Cell Biology"}
        )
        
        print(f"\n💾 MEMORY STATS:")
        print(f"   - Operation: {result['mem_ops']}")
        print(f"   - Items saved: {len(result['memory_items'])}")
        print(f"   - Conversation turns: {result['turns']}")
        print(f"   - Memories recalled: {len(result['recalled_memories'])}")
        
        # Small delay for readability
        await asyncio.sleep(0.5)
    
    print(f"\n{'='*60}")
    print("CONVERSATION COMPLETE")
    print(f"{'='*60}\n")
    
    # Show final state
    print("📊 FINAL MEMORY STATE:")
    print(f"   - Total conversation summary: {len(memory_ops.summary)} chars")
    print(f"   - Remaining history turns: {len(memory_ops.chat_history)}")
    
    # Demonstrate memory search
    print("\n\n🔍 TESTING MEMORY SEARCH:")
    test_queries = [
        "What is photosynthesis?",
        "Tell me about respiration",
        "What are mitochondria?"
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        memories = memory_ops.memory_manager.search_recall_memories(query)
        print(f"   Found {len(memories)} relevant memories")
        if memories:
            print(f"   Top result: {memories[0].page_content[:80]}...")

if __name__ == "__main__":
    # Run the example
    asyncio.run(example_conversation())

