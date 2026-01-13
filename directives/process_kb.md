# SOP: Processing Knowledge Base Files

This directive outlines the process for adding new information to the Dermaglow RAG system.

## Process Flow
1. **Upload**:
   - Use the `/admin/upload` route.
   - Authenticate via Basic Auth.
2. **Storage**:
   - File is saved locally in `uploads/`.
   - **TODO**: Implement Gemini File API upload for long-term storage and better RAG performance.
3. **Indexing**:
   - Save the `file_uri` in the `knowledge_base` table.
   - These URIs are passed to the Gemini handler during every webhook interaction.
