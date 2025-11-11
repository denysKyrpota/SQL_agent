# SQL AI Agent - Frontend

React + TypeScript frontend for the SQL AI Agent application.

## Features

- 🔐 **Authentication**: Login/logout with session management
- 🤖 **Natural Language Queries**: Convert questions to SQL
- 📊 **Results Display**: Paginated table view with metrics
- 📥 **CSV Export**: Download query results
- 🎨 **Modern UI**: Clean, responsive design
- ♿ **Accessible**: WCAG compliant components

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Routing**: React Router v6
- **Styling**: CSS Modules
- **API Client**: Native Fetch API

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables (optional)
cp .env.example .env
```

### Development

```bash
# Start development server (with hot reload)
npm run dev

# Frontend will be available at http://localhost:3000
# API calls will be proxied to http://localhost:8000
```

### Build

```bash
# Type check
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── Button/
│   │   ├── ErrorBoundary/
│   │   ├── Pagination/
│   │   ├── ProtectedRoute/
│   │   ├── TextArea/
│   │   └── Toast/
│   ├── context/            # React contexts
│   │   └── AuthContext.tsx
│   ├── hooks/              # Custom React hooks
│   │   └── useAuth.ts
│   ├── services/           # API service layer
│   │   ├── apiClient.ts    # Base fetch wrapper
│   │   ├── authService.ts  # Auth endpoints
│   │   ├── queryService.ts # Query endpoints
│   │   └── adminService.ts # Admin endpoints
│   ├── types/              # TypeScript type definitions
│   │   ├── api.ts          # API request/response types
│   │   ├── common.ts       # Common types
│   │   ├── models.ts       # Data models
│   │   └── database.types.ts # Auto-generated DB types
│   ├── views/              # Page-level components
│   │   ├── LoginView/      # Login page
│   │   └── QueryInterfaceView/ # Main query interface
│   ├── App.tsx             # Main app with routing
│   ├── main.tsx            # Application entry point
│   └── index.css           # Global styles
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## API Integration

The frontend communicates with the backend via a RESTful API:

### Authentication

- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/session` - Get current session

### Queries

- `POST /api/queries` - Submit natural language query
- `GET /api/queries/{id}` - Get query details
- `GET /api/queries` - List queries (with pagination)
- `POST /api/queries/{id}/execute` - Execute generated SQL
- `GET /api/queries/{id}/results` - Get paginated results
- `GET /api/queries/{id}/export` - Export CSV
- `POST /api/queries/{id}/rerun` - Re-run query

### Admin (Admin role required)

- `POST /api/admin/schema/refresh` - Refresh schema snapshot
- `POST /api/admin/kb/reload` - Reload knowledge base
- `GET /api/admin/metrics` - Get system metrics

## Authentication Flow

1. User enters credentials on `/login`
2. Frontend calls `POST /api/auth/login`
3. Backend validates and creates session (cookie-based)
4. Cookie automatically included in subsequent requests
5. `AuthContext` manages user state globally
6. `ProtectedRoute` guards authenticated routes
7. On 401 error, user redirected to `/login`

## Environment Variables

- `REACT_APP_API_BASE_URL` - API base URL (default: `/api`)
- `VITE_PORT` - Development server port (default: `3000`)
- `VITE_API_URL` - Backend URL for proxy (default: `http://localhost:8000`)

## Development Notes

### Path Aliases

TypeScript is configured with `@/` alias pointing to `src/`:

```typescript
import { useAuth } from '@/hooks/useAuth';
import Button from '@/components/Button';
```

### API Proxy

In development, Vite proxies `/api/*` requests to `http://localhost:8000` to avoid CORS issues.

### Type Safety

- All API requests/responses are fully typed
- Database types auto-generated from SQLAlchemy models
- Strict TypeScript configuration enabled

### State Management

- Authentication state managed via `AuthContext`
- Component-local state with `useState`
- No external state management library needed

## Testing

```bash
# Run tests (when implemented)
npm test

# Run linter
npm run lint
```

## Production Deployment

1. Build the frontend: `npm run build`
2. Serve `dist/` directory with a static file server or CDN
3. Configure API proxy/CORS on production server
4. Set production environment variables

## Troubleshooting

### Port already in use

Change the port in `vite.config.ts` or `.env`:

```env
VITE_PORT=3001
```

### API calls failing

1. Ensure backend is running on `http://localhost:8000`
2. Check Vite proxy configuration in `vite.config.ts`
3. Verify CORS settings in backend

### TypeScript errors

```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Rebuild types
npm run type-check
```

## Contributing

1. Follow existing code style
2. Use TypeScript strictly (no `any` types)
3. Add comments for complex logic
4. Test all API integrations
5. Ensure accessibility standards

## License

Private/Proprietary
