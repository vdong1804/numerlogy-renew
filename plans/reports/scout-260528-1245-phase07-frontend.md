# Scout Report: Next.js Frontend Integration Patterns — Phase 07 (Admin Chatbot UI)

**Date:** 2026-05-28  
**Project:** Numerology Landing Page (Next.js 13)  
**Scope:** Admin layout, chat modules, form patterns, API integration, UI libraries  
**Target:** 5 admin pages + 5 components for Phase 07 Chatbot RAG Admin Tuning UI

---

## 1. Admin Layout + Structure

### Existing Admin Pages
Located in `src/pages/admin/`:
- **Dashboard:** `/admin` (stats + charts + shortcuts)
- **Users:** `/admin/users/`, `[id].tsx`
- **News:** `/admin/news/`, `new.tsx`, `[id].tsx`
- **Banks:** `/admin/banks/`, `new.tsx`, `[id].tsx`
- **Payments:** `/admin/payments/`, `[id].tsx`
- **Products:** `/admin/products/`, `new.tsx`, `[id].tsx`
- **Orders:** `/admin/orders/`, `[id].tsx`
- **Packages:** `/admin/packages/`, `new.tsx`, `[id].tsx`
- **Content:** `/admin/content/[resource]/`, `new.tsx`, `[id].tsx` (dynamic)
- **Webhook Events:** `/admin/webhook-events/`
- **Admin Login:** `/admin/login.tsx`

### Admin Layout Component
**File:** `src/components/admin/admin-layout.tsx` (lines 1-80+)

**Structure:**
```tsx
interface AdminLayoutProps {
  children: React.ReactNode
  title?: string
}

export default function AdminLayout({ children, title }: AdminLayoutProps) {
  const { user, loading, logout } = useAdminAuth()
  // Sidebar + Topbar + Command Palette (Cmd/K) + Dark Mode
  // Returns null if !user (redirected by hook)
}
```

**Layout Shell:**
- Desktop sidebar (hidden md:flex, w-64 sticky)
- Mobile sidebar (Sheet on <768px)
- Main content area (flex-1, min-w-0)
- Responsive wrapper with AdminThemeProvider + ToastProvider

**Child Rendering:** `{children}` rendered in flex-1 column after topbar

### Auth Guard
**File:** `src/lib/admin-auth.ts`

**Hook Signature:**
```tsx
export function useAdminAuth(): UseAdminAuthReturn {
  user: AdminUser | null
  loading: boolean
  logout: () => void
}
```

**Guard Mechanism:**
- Reads token from `localStorage['admin_access_token']`
- On mount: calls `GET /auth/me` to verify `is_superuser`
- If no token or `!is_superuser`: redirects to `/admin/login`
- On 401: clears token & redirects

### Admin Navigation
**Files:** 
- `src/components/admin/admin-nav-config.ts` (config only—source of truth)
- `src/components/admin/admin-sidebar-nav.tsx` (component)

**Config Structure:**
```tsx
export const ADMIN_NAV_GROUPS: AdminNavGroup[] = [
  {
    id: 'content',
    label: 'Nội dung Thần Số Học',
    icon: BookOpen,
    collapsible: true,
    items: [...]
  },
  { id: 'news', label: 'Tin tức', icon: Newspaper, items: [...] },
  { id: 'users', label: 'Người dùng', icon: Users, items: [...] },
  // ...more groups
]
```

**To Add Chatbot Section:**
Add to `ADMIN_NAV_GROUPS` in `admin-nav-config.ts`:
```tsx
{
  id: 'chatbot',
  label: 'Chatbot RAG',
  icon: MessageSquare,
  items: [
    { href: '/admin/chatbot', label: 'Dashboard' },
    { href: '/admin/chatbot/kb', label: 'Knowledge Base' },
    { href: '/admin/chatbot/settings', label: 'Cài đặt' },
    { href: '/admin/chatbot/analytics', label: 'Phân tích' },
  ]
}
```

---

## 2. Existing Chat UI (Phase 04)

### Chat Pages
**File:** `src/pages/chat.tsx` (entry point)

**Structure:**
```tsx
export default function ChatPage() {
  const { user, loading } = useUserAuth()  // Auth guard
  if (!loading && !user) router.replace(`/login?next=/chat`)
  return <Main meta={<Meta ... />}><ChatLayout /></Main>
}
```
Wraps ChatLayout in Main (public header/footer).

### Chat Modules
**Location:** `src/modules/chat/`

**Components:**
- `ChatLayout.tsx` — 3-column shell (sidebar | thread | citations drawer)
- `parts/ConversationSidebar.tsx` — conversation list, create, delete
- `parts/MessageThread.tsx` — message history display
- `parts/MessageInput.tsx` — user input + PDF upload button
- `parts/MessageMarkdown.tsx` — markdown rendering with syntax highlighting
- `parts/CitationDrawer.tsx` — citations sidebar drawer
- `parts/QuotaBadge.tsx` — quota display (free/addon status)
- `parts/UpsellModal.tsx` — upgrade modal
- `parts/PdfUploadButton.tsx` — file picker

**Hooks:**
- `use-chat-stream.ts` — SSE consumer for streaming responses
- `use-conversations.ts` — conversation CRUD
- `use-messages.ts` — message list + append
- `use-pdf-upload.ts` — multipart PDF upload
- `use-quota.ts` — quota fetch + refresh
- `use-rate-limit-countdown.ts` — rate-limit timer

### API Client Pattern
**File:** `src/modules/chat/api/chat-api.ts`

**Base Config:**
```tsx
async function getData<T>(path: string): Promise<T> {
  const env = await getJson<{ data: T }>(path)
  return env.data
}
```
Response envelope: `{ data: T, ... }` (unwrapped locally via getData)

**Example Call (Quota):**
```tsx
export async function fetchQuota(): Promise<Quota> {
  const raw = await getData<QuotaRaw>('/chat/quota')
  return toQuota(raw)  // camelCase transform
}
```

**File Upload Pattern:**
```tsx
export async function uploadPdf(convId: number, file: File): Promise<{ pdfContextId: number }> {
  const form = new FormData()
  form.append('file', file)
  const res = await userFetch(`/api/chat/conversations/${convId}/upload-pdf`, {
    method: 'POST',
    body: form
  })
  return res.json()
}
```

### JWT Attachment
**File:** `src/lib/user-api.ts`

**Mechanism:**
```tsx
export async function userFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = getToken()  // from cookies['access_token']
  const headers = {
    ...(init.headers as Record<string, string>),
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  }
  const res = await fetch(`${API_BASE}${path}`, { ...init, headers })
  if (res.status === 401) handleUnauthorized()
  return res
}
```

Token source: `Cookies.get('access_token')` (via js-cookie)

---

## 3. UI Library + Conventions

### UI Library Stack
1. **shadcn/ui** (custom Radix UI + Tailwind components)
2. **Radix UI** primitives (`@radix-ui/*`)
3. **Tailwind CSS** 3.4.14
4. **Lucide React** — icons (0.456.0)
5. **Class Variance Authority (CVA)** — component variants
6. **Sonner** — toast notifications

### Component Example
**File:** `src/components/ui/button.tsx`

```tsx
const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap ...',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: '...',
        ghost: '...',
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 ...',
        lg: '
