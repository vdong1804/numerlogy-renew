# Design Guidelines

**Version:** 1.0  
**Last Updated:** 2026-05-25

---

## Admin UI Design Patterns

### Language & Localization
- **Primary Language:** Vietnamese
- **All Admin Labels:** Vietnamese (no English in forms, menus, or buttons)
- **Error Messages:** Vietnamese, clear and actionable
- **Date Format:** DD/MM/YYYY (Vietnamese standard)
- **Number Format:** Comma for thousands (1.234.567 or 1,234,567)

**Example Label Mapping:**
| English | Vietnamese | Usage |
|---------|-----------|-------|
| Content | Nội dung | Content editor heading |
| Title | Tiêu đề | Form field label |
| Description | Mô tả | Form field label |
| Save | Lưu | Submit button |
| Delete | Xóa | Delete button |
| Cancel | Hủy | Cancel button |
| Edit | Chỉnh sửa | Edit action |
| Create | Tạo mới | Create action |
| User | Người dùng | User resource |
| Payment | Thanh toán | Payment resource |
| Approved | Được phê duyệt | Status badge |
| Pending | Chờ xử lý | Status badge |
| Rejected | Từ chối | Status badge |

---

## Frontend Architecture (Next.js Pages Router)

### Routing Pattern
- **Convention:** Pages Router (current, not App Router)
- **Dynamic Routes:** `[param].tsx` or `[...slug].tsx` for catch-all
- **Query Strings:** `useRouter().query` (not URL params)
- **Example:** `/admin/content/attitude-number/42` → `pages/admin/content/[resource]/[id].tsx`

### Folder Structure
```
src/pages/
├── index.tsx              # Landing page
├── admin/
│   ├── index.tsx          # Dashboard
│   ├── login.tsx          # Login page
│   ├── content/
│   │   ├── [resource]/
│   │   │   ├── index.tsx  # List
│   │   │   ├── new.tsx    # Create
│   │   │   └── [id].tsx   # Edit
│   ├── users/
│   │   ├── index.tsx
│   │   └── [id].tsx
│   ├── news/
│   ├── packages/
│   ├── banks/
│   └── payments/
└── [public pages...]
```

### Data Fetching
- **Pattern:** `useEffect` + `getJson()` (custom hook)
- **No getStaticProps/getServerSideProps** in admin (all client-side auth)
- **Error Handling:** Try-catch in useEffect, set error state
- **Loading State:** Boolean `isLoading` flag

**Example:**
```tsx
const [data, setData] = useState(null);
const [isLoading, setIsLoading] = useState(false);
const [error, setError] = useState<string | null>(null);

useEffect(() => {
  async function fetchData() {
    try {
      setIsLoading(true);
      const result = await getJson('/admin/users/42');
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error loading data');
    } finally {
      setIsLoading(false);
    }
  }
  fetchData();
}, []);
```

---

## Rich Text Editor (TipTap)

### Configuration
- **Library:** @tiptap/react v2.6.0
- **Starter Kit:** StarterKit extension (bold, italic, heading, list, blockquote, code block, etc.)
- **Custom Extensions:** Image, Link, Table (with rows, cells, headers)

### Toolbar Features
```
| Bold | Italic | Underline | Strikethrough |
| Heading 1 | Heading 2 | Heading 3 |
| Bullet List | Ordered List | Blockquote |
| Code Block | Horizontal Rule |
| Image (Upload) | Link | Table |
| Undo | Redo | Source View (Toggle) |
```

### Image Upload Handling
- **Endpoint:** `POST /admin/upload` (multipart/form-data)
- **Response:** `{url: "/media/images/abc123.jpg", ...}`
- **Validation:** MIME type (image/*), max 5MB
- **Storage:** Nginx volume mount at `/media/`
- **Serve:** Nginx static path (not app download endpoint)

### Source View
- **Toggle Button:** "Source" icon in toolbar
- **Purpose:** Edit raw HTML for advanced users
- **Caveat:** Not WYSIWYG when editing HTML directly

**Example Component:**
```tsx
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Image from '@tiptap/extension-image';
import Link from '@tiptap/extension-link';

const RichTextEditor = ({ value, onChange }) => {
  const editor = useEditor({
    extensions: [StarterKit, Image, Link, Table, ...],
    content: value,
    onUpdate: ({ editor }) => onChange(editor.getHTML()),
  });
  
  return <EditorContent editor={editor} />;
};
```

---

## Data Table (TanStack Table v8)

### Features
- **Pagination:** Client-side or server-side (TanStack supports both)
- **Search:** Filter by text input (name, title, etc.)
- **Column Sorting:** Click header to sort ASC/DESC
- **Row Selection:** Checkboxes for multi-select actions (batch delete)
- **Responsive:** Collapse columns on mobile

### Configuration
```tsx
const columns: ColumnDef<ContentItem>[] = [
  {
    id: 'select',
    header: ({ table }) => <Checkbox {...table.getToggleAllRowsSelectedProps()} />,
    cell: ({ row }) => <Checkbox {...row.getToggleSelectedProps()} />,
  },
  {
    accessorKey: 'title',
    header: 'Tiêu đề',
    cell: (info) => info.getValue(),
  },
  {
    accessorKey: 'created_at',
    header: 'Ngày tạo',
    cell: (info) => formatDate(info.getValue()),
  },
  {
    id: 'actions',
    header: 'Hành động',
    cell: ({ row }) => (
      <>
        <Button onClick={() => editRow(row.original)}>Chỉnh sửa</Button>
        <Button onClick={() => deleteRow(row.original)}>Xóa</Button>
      </>
    ),
  },
];
```

### Pagination Pattern
**Backend Response Shape:**
```json
{
  "items": [...],
  "total": 120,
  "limit": 10,
  "offset": 0
}
```

**Frontend Pagination Hook:**
```tsx
const [pagination, setPagination] = useState({ pageIndex: 0, pageSize: 10 });

const fetchData = async (limit, offset) => {
  const result = await getJson(`/admin/content/attitude-number?limit=${limit}&offset=${offset}`);
  setData(result.items);
  setTotal(result.total);
};

useEffect(() => {
  fetchData(pagination.pageSize, pagination.pageIndex * pagination.pageSize);
}, [pagination]);
```

---

## Form Patterns (react-hook-form + Zod)

### Validation Schema
```tsx
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

const contentSchema = z.object({
  title: z.string().min(1, 'Tiêu đề bắt buộc').max(200, 'Tiêu đề quá dài'),
  content: z.string().min(1, 'Nội dung bắt buộc'),
  number: z.number().min(1).max(999),
});

type ContentFormData = z.infer<typeof contentSchema>;
```

### Form Component
```tsx
const form = useForm<ContentFormData>({
  resolver: zodResolver(contentSchema),
  defaultValues: { title: '', content: '', number: 1 },
});

const onSubmit = async (data) => {
  try {
    await postJson('/admin/content/attitude-number', data);
    // Success: navigate or show toast
  } catch (error) {
    // Error: display in form
  }
};

return (
  <form onSubmit={form.handleSubmit(onSubmit)}>
    <input {...form.register('title')} placeholder="Tiêu đề" />
    {form.formState.errors.title && <span className="error">{form.formState.errors.title.message}</span>}
    
    <button type="submit">Lưu</button>
  </form>
);
```

---

## API Response Format

### Success Response (Paginated List)
```json
{
  "items": [
    { "id": 1, "title": "Attitude 1", "content": "...", "created_at": "2026-05-25T10:30:00Z" },
    { "id": 2, "title": "Attitude 2", "content": "...", "created_at": "2026-05-25T10:35:00Z" }
  ],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

### Success Response (Single Object)
```json
{
  "id": 1,
  "title": "Attitude Number 1",
  "content": "<p>Detailed content...</p>",
  "number": 1,
  "created_at": "2026-05-25T10:30:00Z",
  "updated_at": "2026-05-25T10:30:00Z"
}
```

### Error Response
```json
{
  "detail": "Tiêu đề bắt buộc"
}
```

**HTTP Status Codes:**
- 200 OK — Success
- 201 Created — Resource created
- 204 No Content — Successful delete/logout
- 400 Bad Request — Validation error
- 401 Unauthorized — Missing/invalid token
- 403 Forbidden — Insufficient permissions (not superuser)
- 404 Not Found — Resource not found
- 409 Conflict — Duplicate email on register
- 500 Internal Server Error — Bug
- 503 Service Unavailable — External API failure (e.g., vietheart.net timeout)

---

## Error Handling & UX

### Form Validation Feedback
- **Location:** Below or beside input field
- **Color:** Red (#EF4444 or Tailwind `red-500`)
- **Icon:** Optional warning icon
- **Message:** Vietnamese, specific to error type

**Example:**
```tsx
<div className="mb-4">
  <label className="block text-sm font-medium mb-1">Tiêu đề</label>
  <input
    {...form.register('title')}
    className={`border ${form.formState.errors.title ? 'border-red-500' : 'border-gray-300'}`}
  />
  {form.formState.errors.title && (
    <p className="text-red-500 text-sm mt-1">{form.formState.errors.title.message}</p>
  )}
</div>
```

### Toast Notifications (Success/Error)
- **Library:** react-hot-toast or similar
- **Success:** Green background, "Đã lưu thành công"
- **Error:** Red background, error message from API
- **Duration:** 3-4 seconds auto-dismiss

**Example:**
```tsx
import toast from 'react-hot-toast';

const onSubmit = async (data) => {
  try {
    await postJson('/admin/content/attitude-number', data);
    toast.success('Đã lưu thành công');
  } catch (error) {
    toast.error(error.message || 'Lỗi khi lưu');
  }
};
```

### Confirm Dialogs
- **Delete Action:** Always show confirm dialog before DELETE
- **Modal:** Title, message, cancel/confirm buttons
- **Danger Variant:** Red confirm button for destructive actions

**Example:**
```tsx
const [confirmOpen, setConfirmOpen] = useState(false);

<ConfirmDialog
  title="Xóa nội dung?"
  message="Hành động này không thể hoàn tác."
  onConfirm={() => {
    deleteJson(`/admin/content/attitude-number/${id}`);
    setConfirmOpen(false);
  }}
  onCancel={() => setConfirmOpen(false)}
  isOpen={confirmOpen}
  isDanger
/>
```

---

## Accessibility & Keyboard Navigation

### ARIA Labels
- **Form Inputs:** `<label htmlFor="...">Tiêu đề</label>`
- **Buttons:** `aria-label` if icon-only button
- **Dialogs:** `aria-labelledby`, `aria-describedby`
- **Tables:** `aria-label` on action buttons per row

### Keyboard Support
- **Tab Navigation:** All interactive elements focusable in logical order
- **Enter:** Submit form, confirm dialog
- **Escape:** Close modal, cancel operation
- **Arrow Keys:** Navigate table rows (optional enhancement)

### Color Contrast
- **Minimum:** 4.5:1 for normal text, 3:1 for large text
- **Test:** Use axe DevTools or WAVE browser extension

---

## Styling Conventions (Tailwind CSS)

### Spacing Scale
```
p-0, p-1, p-2, p-3, p-4, p-6, p-8, p-12, p-16
(0, 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px)
```

### Color Palette
```
Primary: blue-600, blue-500
Success: green-500, green-600
Error: red-500, red-600
Warning: yellow-500, yellow-600
Neutral: gray-100 to gray-900
```

### Responsive Breakpoints
```
sm: 640px
md: 768px
lg: 1024px
xl: 1280px
2xl: 1536px
```

**Usage:** `md:grid-cols-2 lg:grid-cols-3` (stack on mobile, 2 cols at md, 3 cols at lg)

### Example Component
```tsx
<div className="p-4 md:p-6 lg:p-8">
  <h1 className="text-2xl font-bold mb-4 text-gray-900">Quản lý nội dung</h1>
  
  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      {/* Content */}
    </div>
  </div>
  
  <button className="mt-6 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
    Lưu
  </button>
</div>
```

---

## Backend API Response Design

### Consistency Principles
- **Always return structured JSON** (never plaintext or HTML)
- **Use snake_case for API keys** (camelCase in frontend TS types)
- **Timestamps in ISO 8601 format** (YYYY-MM-DDTHH:mm:ssZ)
- **Numeric IDs as integers** (not strings)
- **Booleans as true/false** (not 0/1)

### Example API Responses

**Create (201):**
```json
{
  "id": 42,
  "code": 1,
  "title": "Attitude Number 1",
  "content": "<p>New content...</p>",
  "number_page": 1,
  "created_at": "2026-05-25T12:30:45Z"
}
```

**List (200):**
```json
{
  "items": [
    { "id": 1, "title": "Attitude 1", ... },
    { "id": 2, "title": "Attitude 2", ... }
  ],
  "total": 120,
  "limit": 10,
  "offset": 0
}
```

**Update (200):**
```json
{
  "id": 42,
  "code": 1,
  "title": "Attitude Number 1 (Updated)",
  "content": "<p>Updated content...</p>",
  "updated_at": "2026-05-25T13:00:00Z"
}
```

**Delete (204):** No body returned

**Error (400, 403, 404, etc.):**
```json
{
  "detail": "Tiêu đề bắt buộc"
}
```

---

## Pagination Convention

### Query Parameters
- `limit`: Items per page (default 10, max 100)
- `offset`: Starting position (0-indexed)

**Example:** `GET /admin/content/attitude-number?limit=20&offset=40`

### Response Shape
```json
{
  "items": [...],
  "total": 120,
  "limit": 20,
  "offset": 40
}
```

### Frontend Calculation
```tsx
const page = Math.floor(offset / limit) + 1;  // 3
const totalPages = Math.ceil(total / limit);   // 6
```

---

## Performance & UX Best Practices

### Image Optimization
- Use `next/image` component (auto optimization)
- Lazy load images below fold
- Provide explicit width/height to prevent layout shift

### Debouncing Search
```tsx
const [searchTerm, setSearchTerm] = useState('');

useEffect(() => {
  const timer = setTimeout(() => {
    fetchData(searchTerm);
  }, 300);  // 300ms delay
  
  return () => clearTimeout(timer);
}, [searchTerm]);

return <input onChange={(e) => setSearchTerm(e.target.value)} />;
```

### Loading Skeletons
- Show skeleton UI while fetching (better UX than blank)
- Match final layout to prevent layout shift

### Caching Strategy
- Cache API responses in state (5-10 min) to reduce requests
- Invalidate on form submit or manual refresh
- Allow user-initiated refresh button

