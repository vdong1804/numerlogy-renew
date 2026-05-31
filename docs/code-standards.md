# Code Standards

**Version:** 1.0  
**Last Updated:** 2026-05-25

---

## Python Backend (FastAPI)

### Language & Version
- **Python:** 3.12+
- **Style:** PEP 8 + ruff linting (enforce via CI)
- **Type Hints:** mypy strict mode (all functions typed)
- **Async:** Use `async`/`await` everywhere; no sync I/O in routes

### File Structure & Naming
- **Files:** `snake_case.py` (e.g., `numerology_sums.py`, `user_service.py`)
- **Classes:** `PascalCase` (e.g., `UserService`, `NumerologyContent`)
- **Functions:** `snake_case` (e.g., `calculate_numerology_numbers`)
- **Constants:** `UPPER_CASE` (e.g., `MAX_QUOTA`, `JWT_SECRET`)
- **File Size:** Keep ≤200 LOC; split if exceeds (e.g., numerology.py → numerology_sums.py + core package)

### Imports & Organization
```python
# 1. Standard library
from __future__ import annotations
from typing import Optional, List
from datetime import datetime

# 2. Third-party
from sqlalchemy import Column, String
from pydantic import BaseModel, ConfigDict

# 3. Local
from app.db.base import Base
from app.core.security import hash_password
```

### Database Models (SQLAlchemy 2.0)

**Pattern:** Use `Mapped[]` + `mapped_column()` (declarative style)

```python
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    
    # Relationships
    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False)
```

**Mixins:** Use `TimestampMixin` for `created_at` + `updated_at` fields

```python
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
```

### Pydantic v2 Schemas

**Pattern:** Use `ConfigDict` + model_config class variable

```python
from pydantic import BaseModel, ConfigDict, Field

class UserCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # Allows .from_orm()
    
    email: str
    password: str
    first_name: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: str
    first_name: Optional[str] = None
```

### Async/Await

**Routes:** Always async
```python
@router.get("/api/data")
async def get_data(db: AsyncSession = Depends(get_db)) -> dict:
    result = await db.execute(select(SomeModel))
    return {"data": result.scalars().all()}
```

**Database calls:** Use async SQLAlchemy
```python
async def get_user_by_email(db: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
```

**I/O (HTTP, file, etc.):**
```python
# ✅ Good: async httpx for external APIs
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com/data")

# ❌ Bad: requests (blocking)
import requests
response = requests.get(...)

# ✅ Good: asyncio.to_thread for CPU-bound work
import asyncio
pdf = await asyncio.to_thread(render_pdf, html_string)
```

### Error Handling

**Use FastAPI HTTPException**
```python
from fastapi import HTTPException

async def get_user(user_id: int, db: AsyncSession):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

**Never let exceptions bubble without context**
```python
try:
    pdf = await wkhtmltopdf.render(html)
except Exception as e:
    raise HTTPException(status_code=500, detail="PDF render failed") from e
```

### Server-Sent Events (SSE)

**Pattern:** Streaming responses using HTTP/1.1 Server-Sent Events

**Key Components:**
- **sse_event() helper:** `sse_event(event_name: str, data: dict) -> bytes` formats SSE frames as `event: name\ndata: {...}\n\n`
- **StreamingResponse:** FastAPI's `StreamingResponse` wraps async generator, handles chunk delivery
- **Nginx header:** Set `X-Accel-Buffering: no` in location regex to disable upstream buffering (required for real-time delivery)
- **Async generator:** Yield byte chunks from LLM stream iterator (via thread bridge if sync SDK)
- **Client keepalive:** HTTP/1.1 persistent connection required; nginx `proxy_read_timeout` (e.g., 300s) for long-lived streams

**Example (chat endpoint):**
```python
@router.post("/stream")
async def stream_message(...) -> StreamingResponse:
    # Ownership check, persist user message (before generator starts)
    async def _event_gen():
        # Retrieval → LLM stream → yield delta events
        async for token in llm.generate_stream(...):
            yield sse_event("delta", {"token": token})
        # Final: citations → done
        yield sse_event("citations", {"citations": [...]})
        yield sse_event("done", {"message_id": 42, ...})
    
    return StreamingResponse(
        _event_gen(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}
    )
```

**Frontend consumer pattern:**
- Fetch with `Accept: text/event-stream` + Bearer token
- Read response body via `getReader()`; decode with `TextDecoder({ stream: true })`
- Parse frames on `\n\n` boundaries (hold incomplete trailing frame in buffer)
- Dispatch by event name; handle `error` events as stream abort

### Idempotent Payment Fulfillment (Phase 05+)

**Pattern:** Ensure payment fulfillment (add-on grants, quota increases) can be safely retried without duplication.

**Design:**
1. **Unique idempotency key:** Payment ID stored in fulfillment table (e.g., `chat_addon_purchases.payment_id` UNIQUE)
2. **Check-before-insert:** Before granting resource, query for existing fulfillment record by payment ID
3. **Atomic insert-or-retrieve:** If exists, return success (already fulfilled); if not, insert and return
4. **Example (chat addon):**
   ```python
   async def fulfill_chat_addon(db, payment_id, user_id, package_id):
       # Check if already fulfilled
       existing = await db.execute(
           select(ChatAddonPurchase).where(
               ChatAddonPurchase.payment_id == payment_id
           )
       )
       if existing.scalar_one_or_none():
           return {"status": "already_fulfilled"}
       
       # New fulfillment: insert addon with TTL
       addon = ChatAddonPurchase(
           user_id=user_id,
           package_id=package_id,
           payment_id=payment_id,
           remaining_messages=package.message_count,
           expires_at=datetime.now(tz=UTC) + timedelta(days=package.validity_days)
       )
       db.add(addon)
       await db.commit()
       return {"status": "fulfilled", "addon_id": addon.id}
   ```

**Rationale:** Webhook retries (especially SePay + network jitter) can trigger fulfillment multiple times; idempotency prevents duplicate message grants.

---

### Response Format

**Collections:**
```json
{
  "items": [...],
  "total": 42,
  "limit": 10,
  "offset": 0
}
```

**Single objects:**
```json
{
  "id": 1,
  "email": "user@example.com",
  ...
}
```

**Errors:**
```json
{
  "detail": "User not found"
}
```

### Testing

**Test File Naming:** `test_*.py` or `*_test.py` (pytest discovers both)

**Example Structure:**
```python
# tests/test_user_service.py
import pytest
from app.services.user_service import UserService

@pytest.mark.asyncio
async def test_create_user(db_session):
    service = UserService(db_session)
    user = await service.create_user(email="test@example.com", password="pass")
    assert user.email == "test@example.com"

@pytest.mark.asyncio
async def test_create_user_duplicate_email(db_session):
    await db_session.execute(insert(User).values(email="dup@example.com"))
    with pytest.raises(ValueError, match="already exists"):
        service = UserService(db_session)
        await service.create_user(email="dup@example.com", password="pass")
```

**Coverage Goal:** ≥70% (critical paths, edge cases)

---

## TypeScript/Next.js Frontend

### Language & Version
- **TypeScript:** 5.0+, strict mode
- **React:** 18+, functional components + hooks
- **Next.js:** Pages Router (current; App Router future)
- **Styling:** Tailwind CSS (existing)

### File Naming
- **Components:** `PascalCase.tsx` (e.g., `AdminLayout.tsx`)
- **Pages:** `kebab-case.tsx` (e.g., `content-form.tsx`) or `[dynamic].tsx`
- **Utils/Hooks:** `kebab-case.ts` (e.g., `use-admin-auth.ts`, `admin-api.ts`)
- **File Size:** Keep ≤200 LOC; split large components

### Component Patterns

**Functional + Hooks:**
```tsx
import { FC, useState, useEffect } from 'react';

interface AdminLayoutProps {
  children: React.ReactNode;
}

const AdminLayout: FC<AdminLayoutProps> = ({ children }) => {
  const [isAuth, setIsAuth] = useState(false);
  
  useEffect(() => {
    // Setup
  }, []);
  
  return <div>{children}</div>;
};

export default AdminLayout;
```

**Custom Hooks:**
```tsx
// hooks/use-admin-auth.ts
function useAdminAuth() {
  const [user, setUser] = useState(null);
  
  useEffect(() => {
    // Fetch /auth/me
  }, []);
  
  return { user, isLoading: !user };
}
```

### Forms & Validation

**Pattern:** react-hook-form + Zod (admin pages)

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  title: z.string().min(1, 'Required'),
  content: z.string(),
});

export function ContentForm() {
  const form = useForm({
    resolver: zodResolver(schema),
  });
  
  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <input {...form.register('title')} />
      {form.formState.errors.title && <span>{form.formState.errors.title.message}</span>}
    </form>
  );
}
```

### API Calls

**Pattern:** Bearer token in headers, error handling

```tsx
// lib/admin-api.ts
export async function getJson(path: string) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('admin_access_token')}`,
    },
  });
  if (res.status === 401) {
    // Logout
  }
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// Usage in component
const [data, setData] = useState(null);
useEffect(() => {
  getJson('/admin/users/42').then(setData).catch(console.error);
}, []);
```

### Naming Conventions
- **State variables:** `isLoading`, `hasError`, `isOpen`, etc. (boolean prefix: is/has)
- **Event handlers:** `onClick`, `onSubmit`, etc. (camelCase on-prefix)
- **Constants:** `ADMIN_BASE_URL`, `MAX_FILE_SIZE` (UPPER_CASE)
- **Interfaces/Types:** `PascalCase` suffix `Props` for component props

---

## Git & Commits

### Conventional Commits

**Format:** `<type>(<scope>): <subject>`

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code restructure (no behavior change)
- `test:` Test suite
- `chore:` Build, deps, etc.

**Examples:**
```
feat(auth): add Google OAuth callback handler
fix(numerology): handle master number 33 edge case
docs: add system architecture diagram
refactor(services): split numerology_service.py into smaller modules
test(api): add payment approval integration tests
chore(deps): upgrade FastAPI to 0.115.1
```

**Commit Message Style:**
- Use imperative mood ("add feature", not "added feature")
- No AI references
- Under 72 characters for subject line
- Wrap body at 72 characters
- Reference issue numbers if applicable

### Pre-commit Checks

**Before push, run:**
```bash
# Python backend
cd numerology-api
ruff check app/  # Linting
mypy app/        # Type checking
pytest tests/    # Unit tests

# TypeScript frontend
cd Numerology-Landing-Page
npm run lint     # ESLint
npm run type-check  # TypeScript
npm run test     # Jest/Vitest
```

**No forced push to main/dev branches**

---

## Security & Best Practices

### Password Storage
- Use `bcrypt` via `passlib` (never plain text)
- Cost factor: 12 (default for passlib)

### Secrets Management
- Store in `.env` (never commit)
- Load via `pydantic-settings` (FastAPI) or `.env.local` (Next.js)
- `.env.example` with placeholder values (safe to commit)

### SQL Injection Prevention
- Use SQLAlchemy parameterized queries (always)
- Never `f"SELECT * FROM table WHERE id = {user_id}"`

### CORS & CSRF
- Whitelist frontend domains in FastAPI CORS config
- HTTPS in production (redirected by Nginx)

### File Uploads
- Validate MIME type + size (server-side)
- Generate random filename (prevent enumeration)
- Serve via Nginx static mount (prevent code execution)

---

## Linting & Formatting

### Python (ruff)

**Config:** `pyproject.toml`
```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "W", "F", "I"]  # pycodestyle, warnings, pyflakes, isort
```

**Commands:**
```bash
ruff check app/     # Lint
ruff format app/    # Auto-format
```

### TypeScript (ESLint)

**Config:** `.eslintrc.json` (existing)

**Commands:**
```bash
npm run lint       # Check
npm run lint -- --fix  # Auto-fix
```

---

## Documentation in Code

### Docstrings (Python)

**Style:** Google-style (one-liner for simple functions)

```python
def calculate_sum(numbers: list[int]) -> int:
    """Sum a list of integers."""
    return sum(numbers)

def fetch_numerology_content(db: AsyncSession, code: str, number: int) -> Optional[NumerologyContent]:
    """Fetch numerology content by code and number.
    
    Args:
        db: Database session.
        code: Content code (e.g., 'attitude_number').
        number: Number value (1-9 or master: 11, 22, 33).
    
    Returns:
        NumerologyContent model or None if not found.
    """
```

### Comments (Code)

**When:** Edge cases, non-obvious logic, TODO markers

```python
# Master number redirect: 11→2, 22→4, 33→6
if number in (11, 22, 33):
    number = sum(int(d) for d in str(number))

# TODO: Cache numerology content in Redis post-launch (phase post-launch)
```

---

## Dependency Management

### Python (`pyproject.toml`)

**Frozen versions for prod, flexible for dev:**
```toml
dependencies = [
    "fastapi==0.115.0",
    "sqlalchemy==2.0.30",
    "pydantic==2.5.0",
    "pydantic-settings==2.1.0",
    ...
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "mypy",
    "ruff",
    ...
]
```

### JavaScript (`package.json`)

**Caret ranges for most packages:**
```json
{
  "dependencies": {
    "react": "^18.0.0",
    "next": "^14.0.0",
    "tailwindcss": "^3.0.0"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "eslint": "^8.0.0"
  }
}
```

---

## Performance Guidelines

### Backend
- DB queries: Minimize N+1 (use `SELECT ... IN (...)` for batch fetches)
- Route response time: <500ms target (excluding PDF render ~3-5s)
- PDF generation: Queue if >1s per request (future optimization)

### Frontend
- Bundle size: Keep main entry <100KB (gzipped)
- Image optimization: Use next/image (automatic optimization)
- Code splitting: Lazy-load admin routes

---

## Accessibility & UX

### Admin UI
- Vietnamese labels throughout (no English in forms)
- Aria labels on form inputs
- Error messages near inputs (red text, icon)
- Keyboard navigation (Tab, Enter, Escape)

### Public Pages
- Semantic HTML (main, section, article, etc.)
- Image alt text (SEO + accessibility)
- Form validation feedback (client + server)

---

## Migration & Backwards Compatibility

### API Versioning
- **Current:** No versioning (v1 implicit in all routes)
- **Future:** Consider `/v2/` only if breaking changes needed
- **Breaking change example:** Response shape change → bump version

### Database Migrations
- Always test rollback: `alembic downgrade -1` before pushing
- Name migrations clearly: `0003_add_user_quota_tracking.py`
- Avoid data migrations in Alembic (use seed scripts instead)

