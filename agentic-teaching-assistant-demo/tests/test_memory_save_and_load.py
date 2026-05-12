"""
Test Memory JSON Persistence

This test focuses specifically on saving and loading memories to/from JSON files.
Tests file I/O operations, data integrity, and edge cases.
"""

import asyncio
import sys
import json
import shutil
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from agent_memory import get_memory_ops, clear_user_memory
from colorama import Fore
import pytest


class TestMemoryJSONPersistence:
    """Test suite for JSON persistence functionality"""
    
    @pytest.fixture
    def test_username(self):
        """Provide a test username"""
        return "test_json_user"
    
    @pytest.fixture
    def memory_dir(self, test_username):
        """Provide and cleanup memory directory"""
        mem_dir = Path("mnt") / test_username / "memory"
        yield mem_dir
        # Cleanup after test
        if mem_dir.parent.exists():
            shutil.rmtree(mem_dir.parent)
    
    @pytest.fixture
    def memory_file(self, memory_dir):
        """Provide memory file path"""
        return memory_dir / "conversation_memory.json"
    
    def test_save_memory_to_json(self, test_username, memory_file):
        """Test saving memories to JSON file"""
        print(f"\n{Fore.CYAN}TEST 1: Save Memory to JSON{Fore.RESET}")
        
        # Clear any existing memory
        clear_user_memory(test_username)
        
        # Create memory ops
        memory_ops = get_memory_ops(test_username, rate_limit_delay=1.0)
        
        # Add some memories manually
        memory_handler = memory_ops.memory_manager
        test_memories = [
            "User likes studying biology",
            "User finds photosynthesis interesting",
            "User's favorite topic is cellular respiration"
        ]
        
        docs = memory_handler.save_recall_memory(test_memories)
        
        # Check file was created
        assert memory_file.exists(), "Memory file should exist after saving"
        print(f"{Fore.GREEN}✓ Memory file created: {memory_file}{Fore.RESET}")
        
        # Check file contents
        with open(memory_file, 'r') as f:
            data = json.load(f)
        
        assert "username" in data, "JSON should contain username"
        assert "memories" in data, "JSON should contain memories"
        assert "last_updated" in data, "JSON should contain last_updated"
        assert "summary" in data, "JSON should contain summary"
        
        assert data["username"] == test_username, "Username should match"
        assert len(data["memories"]) == 3, "Should have 3 memories"
        
        print(f"{Fore.GREEN}✓ JSON structure is correct{Fore.RESET}")
        print(f"{Fore.CYAN}  - Username: {data['username']}{Fore.RESET}")
        print(f"{Fore.CYAN}  - Memories: {len(data['memories'])}{Fore.RESET}")
        print(f"{Fore.CYAN}  - Last updated: {data['last_updated']}{Fore.RESET}")
        
        # Check individual memory structure
        for i, mem in enumerate(data["memories"]):
            assert "content" in mem, f"Memory {i} should have content"
            assert "metadata" in mem, f"Memory {i} should have metadata"
            assert "id" in mem, f"Memory {i} should have UUID"
            
            # Check metadata
            assert "user_id" in mem["metadata"], f"Memory {i} should have user_id in metadata"
            assert "timestamp" in mem["metadata"], f"Memory {i} should have timestamp"
            
            print(f"{Fore.CYAN}  Memory {i+1}: {mem['content'][:50]}...{Fore.RESET}")
        
        print(f"{Fore.GREEN}✓ All memories have correct structure{Fore.RESET}")
        
        return data
    
    def test_load_memory_from_json(self, test_username, memory_file):
        """Test loading memories from JSON file"""
        print(f"\n{Fore.CYAN}TEST 2: Load Memory from JSON{Fore.RESET}")
        
        # First save some memories
        clear_user_memory(test_username)
        memory_ops_save = get_memory_ops(test_username, rate_limit_delay=1.0)
        
        test_memories = [
            "User studies computer science",
            "User is learning about algorithms",
            "User prefers Python programming"
        ]
        memory_ops_save.memory_manager.save_recall_memory(test_memories)
        
        print(f"{Fore.YELLOW}Memories saved. Clearing cache...{Fore.RESET}")
        
        # Clear cache to simulate new session
        from agent_memory import _memory_ops_cache
        _memory_ops_cache.clear()
        
        # Load memories in new session
        memory_ops_load = get_memory_ops(test_username, rate_limit_delay=1.0)
        
        # Check memories were loaded
        loaded_memories = memory_ops_load.memory_manager._all_memories
        assert len(loaded_memories) == 3, f"Should load 3 memories, got {len(loaded_memories)}"
        
        print(f"{Fore.GREEN}✓ Loaded {len(loaded_memories)} memories from file{Fore.RESET}")
        
        # Check content matches
        for i, mem in enumerate(loaded_memories):
            assert mem["content"] == test_memories[i], f"Memory {i} content should match"
            print(f"{Fore.CYAN}  Memory {i+1}: {mem['content']}{Fore.RESET}")
        
        print(f"{Fore.GREEN}✓ All memory contents match original{Fore.RESET}")
        
        return memory_ops_load
    
    def test_search_loaded_memories(self, test_username):
        """Test that loaded memories are searchable"""
        print(f"\n{Fore.CYAN}TEST 3: Search Loaded Memories{Fore.RESET}")
        
        # Save memories
        clear_user_memory(test_username)
        memory_ops_save = get_memory_ops(test_username, rate_limit_delay=1.0)
        
        test_memories = [
            "User is studying quantum physics",
            "User finds quantum entanglement fascinating",
            "User is reading about Schrödinger's cat"
        ]
        memory_ops_save.memory_manager.save_recall_memory(test_memories)
        
        # Clear cache and reload
        from agent_memory import _memory_ops_cache
        _memory_ops_cache.clear()
        
        memory_ops_load = get_memory_ops(test_username, rate_limit_delay=1.0)
        
        # Search for quantum-related memories
        search_results = memory_ops_load.memory_manager._search_memories("quantum physics")
        
        assert len(search_results) > 0, "Should find quantum-related memories"
        print(f"{Fore.GREEN}✓ Found {len(search_results)} memories for 'quantum physics'{Fore.RESET}")
        
        for i, result in enumerate(search_results[:3]):
            print(f"{Fore.CYAN}  Result {i+1}: {result[:60]}...{Fore.RESET}")
        
        # Search for specific topic
        cat_results = memory_ops_load.memory_manager._search_memories("Schrödinger's cat")
        assert len(cat_results) > 0, "Should find cat-related memories"
        print(f"{Fore.GREEN}✓ Found {len(cat_results)} memories for 'Schrödinger's cat'{Fore.RESET}")
    
    def test_empty_memories(self, test_username, memory_file):
        """Test behavior with no memories"""
        print(f"\n{Fore.CYAN}TEST 4: Empty Memories{Fore.RESET}")
        
        clear_user_memory(test_username)
        
        # Create memory ops with no memories
        memory_ops = get_memory_ops(test_username, rate_limit_delay=1.0)
        
        # Save should create file even with empty memories
        memory_ops.memory_manager.save_memory_to_file()
        
        assert memory_file.exists(), "File should exist even with no memories"
        print(f"{Fore.GREEN}✓ File created with empty memories{Fore.RESET}")
        
        # Check file contents
        with open(memory_file, 'r') as f:
            data = json.load(f)
        
        assert len(data["memories"]) == 0, "Should have 0 memories"
        print(f"{Fore.GREEN}✓ Empty memories array in JSON{Fore.RESET}")
    
    def test_missing_file(self, test_username):
        """Test behavior when file doesn't exist"""
        print(f"\n{Fore.CYAN}TEST 5: Missing File{Fore.RESET}")
        
        clear_user_memory(test_username)
        
        # Create memory ops without existing file
        memory_ops = get_memory_ops(test_username, rate_limit_delay=1.0)
        
        # Should not error, just have empty memories
        assert len(memory_ops.memory_manager._all_memories) == 0, "Should have 0 memories"
        print(f"{Fore.GREEN}✓ Handles missing file gracefully{Fore.RESET}")
    
    def test_summary_persistence(self, test_username):
        """Test that conversation summary persists"""
        print(f"\n{Fore.CYAN}TEST 6: Summary Persistence{Fore.RESET}")
        
        clear_user_memory(test_username)
        memory_ops = get_memory_ops(test_username, rate_limit_delay=1.0)
        
        # Set a summary
        test_summary = "The user learned about biology and chemistry."
        memory_ops.summary = test_summary
        memory_ops.memory_manager.summary = test_summary
        
        # Save
        memory_ops.memory_manager.save_memory_to_file()
        
        # Clear cache and reload
        from agent_memory import _memory_ops_cache
        _memory_ops_cache.clear()
        
        memory_ops_load = get_memory_ops(test_username, rate_limit_delay=1.0)
        
        # Check summary was loaded
        assert memory_ops_load.summary == test_summary, "Summary should persist"
        print(f"{Fore.GREEN}✓ Summary persisted: {test_summary}{Fore.RESET}")
    
    def test_metadata_persistence(self, test_username):
        """Test that metadata persists correctly"""
        print(f"\n{Fore.CYAN}TEST 7: Metadata Persistence{Fore.RESET}")
        
        clear_user_memory(test_username)
        memory_ops = get_memory_ops(test_username, rate_limit_delay=1.0)
        
        # Add memory with metadata
        memory_ops.memory_manager.save_recall_memory(["Test memory with metadata"])
        
        # Get the saved memory
        saved_memory = memory_ops.memory_manager._all_memories[0]
        original_timestamp = saved_memory["metadata"]["timestamp"]
        original_id = saved_memory["id"]
        
        print(f"{Fore.CYAN}  Original ID: {original_id}{Fore.RESET}")
        print(f"{Fore.CYAN}  Original timestamp: {original_timestamp}{Fore.RESET}")
        
        # Clear and reload
        from agent_memory import _memory_ops_cache
        _memory_ops_cache.clear()
        
        memory_ops_load = get_memory_ops(test_username, rate_limit_delay=1.0)
        loaded_memory = memory_ops_load.memory_manager._all_memories[0]
        
        # Check metadata preserved
        assert loaded_memory["id"] == original_id, "ID should be preserved"
        assert loaded_memory["metadata"]["timestamp"] == original_timestamp, "Timestamp should be preserved"
        assert loaded_memory["metadata"]["user_id"] == test_username, "User ID should be preserved"
        
        print(f"{Fore.GREEN}✓ All metadata preserved correctly{Fore.RESET}")
    
    def test_multiple_users(self):
        """Test that different users have separate files"""
        print(f"\n{Fore.CYAN}TEST 8: Multiple Users{Fore.RESET}")
        
        user1 = "test_user_alice"
        user2 = "test_user_bob"
        
        clear_user_memory(user1)
        clear_user_memory(user2)
        
        # Create memories for user 1
        memory_ops_1 = get_memory_ops(user1, rate_limit_delay=1.0)
        memory_ops_1.memory_manager.save_recall_memory(["Alice likes biology"])
        
        # Create memories for user 2
        memory_ops_2 = get_memory_ops(user2, rate_limit_delay=1.0)
        memory_ops_2.memory_manager.save_recall_memory(["Bob likes chemistry"])
        
        # Check separate files exist
        file1 = memory_ops_1.memory_manager.memory_file
        file2 = memory_ops_2.memory_manager.memory_file
        
        assert file1.exists(), "User 1 file should exist"
        assert file2.exists(), "User 2 file should exist"
        assert file1 != file2, "Files should be different"
        
        print(f"{Fore.GREEN}✓ User 1 file: {file1}{Fore.RESET}")
        print(f"{Fore.GREEN}✓ User 2 file: {file2}{Fore.RESET}")
        
        # Check contents are different
        with open(file1, 'r') as f:
            data1 = json.load(f)
        with open(file2, 'r') as f:
            data2 = json.load(f)
        
        assert data1["username"] == user1, "User 1 data should have correct username"
        assert data2["username"] == user2, "User 2 data should have correct username"
        assert "Alice" in data1["memories"][0]["content"], "User 1 should have Alice memory"
        assert "Bob" in data2["memories"][0]["content"], "User 2 should have Bob memory"
        
        print(f"{Fore.GREEN}✓ Users have separate, isolated memory files{Fore.RESET}")
        
        # Cleanup
        clear_user_memory(user1)
        clear_user_memory(user2)
    
    def test_file_corruption_handling(self, test_username, memory_file):
        """Test handling of corrupted JSON file"""
        print(f"\n{Fore.CYAN}TEST 9: Corrupted File Handling{Fore.RESET}")
        
        clear_user_memory(test_username)
        
        # Create memory directory
        memory_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write corrupted JSON
        with open(memory_file, 'w') as f:
            f.write("{invalid json content")
        
        print(f"{Fore.YELLOW}Created corrupted JSON file{Fore.RESET}")
        
        # Try to load - should handle gracefully
        try:
            memory_ops = get_memory_ops(test_username, rate_limit_delay=1.0)
            # Should have empty memories due to load failure
            assert len(memory_ops.memory_manager._all_memories) == 0, "Should have empty memories on corruption"
            print(f"{Fore.GREEN}✓ Handled corrupted file gracefully{Fore.RESET}")
        except Exception as e:
            print(f"{Fore.RED}✗ Failed to handle corruption: {e}{Fore.RESET}")
            raise


def run_all_tests():
    """Run all tests in order"""
    print(f"\n{Fore.CYAN}{'='*80}{Fore.RESET}")
    print(f"{Fore.CYAN}MEMORY JSON PERSISTENCE TEST SUITE{Fore.RESET}")
    print(f"{Fore.CYAN}{'='*80}{Fore.RESET}\n")
    
    test_suite = TestMemoryJSONPersistence()
    test_username = "test_json_user"
    memory_dir = Path("mnt") / test_username / "memory"
    memory_file = memory_dir / "conversation_memory.json"
    
    try:
        # Test 1: Save to JSON
        test_suite.test_save_memory_to_json(test_username, memory_file)
        
        # Test 2: Load from JSON
        test_suite.test_load_memory_from_json(test_username, memory_file)
        
        # Test 3: Search loaded memories
        test_suite.test_search_loaded_memories(test_username)
        
        # Test 4: Empty memories
        test_suite.test_empty_memories(test_username, memory_file)
        
        # Test 5: Missing file
        test_suite.test_missing_file(test_username)
        
        # Test 6: Summary persistence
        test_suite.test_summary_persistence(test_username)
        
        # Test 7: Metadata persistence
        test_suite.test_metadata_persistence(test_username)
        
        # Test 8: Multiple users
        test_suite.test_multiple_users()
        
        # Test 9: Corruption handling
        test_suite.test_file_corruption_handling(test_username, memory_file)
        
        print(f"\n{Fore.GREEN}{'='*80}{Fore.RESET}")
        print(f"{Fore.GREEN}✓ ALL TESTS PASSED!{Fore.RESET}")
        print(f"{Fore.GREEN}{'='*80}{Fore.RESET}\n")
        
        # Summary
        print(f"{Fore.CYAN}Test Summary:{Fore.RESET}")
        print(f"  ✓ Save memory to JSON")
        print(f"  ✓ Load memory from JSON")
        print(f"  ✓ Search loaded memories")
        print(f"  ✓ Handle empty memories")
        print(f"  ✓ Handle missing files")
        print(f"  ✓ Persist conversation summary")
        print(f"  ✓ Persist metadata (IDs, timestamps)")
        print(f"  ✓ Isolate multiple users")
        print(f"  ✓ Handle corrupted JSON files")
        print()
        
    except Exception as e:
        print(f"\n{Fore.RED}{'='*80}{Fore.RESET}")
        print(f"{Fore.RED}✗ TEST FAILED{Fore.RESET}")
        print(f"{Fore.RED}{'='*80}{Fore.RESET}\n")
        print(f"{Fore.RED}Error: {e}{Fore.RESET}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if memory_dir.parent.exists():
            shutil.rmtree(memory_dir.parent)
        print(f"{Fore.YELLOW}Cleaned up test files{Fore.RESET}")


if __name__ == "__main__":
    # Run with pytest or standalone
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "pytest":
        # Run with pytest
        pytest.main([__file__, "-v"])
    else:
        # Run standalone
        run_all_tests()

