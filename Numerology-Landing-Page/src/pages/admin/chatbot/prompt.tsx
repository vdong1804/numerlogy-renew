/**
 * Admin system prompt editor.
 * Route: /admin/chatbot/prompt
 */
import AdminLayout from '@/components/admin/admin-layout'
import { AdminPageHeader } from '@/components/admin/admin-page-header'
import PromptEditor from '@/modules/admin/chatbot/prompt-editor'

export default function ChatbotPromptPage() {
  return (
    <AdminLayout title="System Prompt">
      <AdminPageHeader
        title="System Prompt"
        description="Override prompt mặc định. Khi không có override, hệ thống dùng prompt cố định trong code để giữ ổn định Gemini prompt cache."
      />
      <PromptEditor />
    </AdminLayout>
  )
}
