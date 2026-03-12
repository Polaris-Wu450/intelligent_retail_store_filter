# RetailOps Frontend (React + Vite)

## Quick Start

### Development Mode

```bash
# Install dependencies
cd frontend
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Production Build

```bash
# Build for production
cd frontend
npm run build
```

This will generate optimized files in `static/dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── components/          # React components
│   │   ├── TabNav.jsx       # Tab navigation
│   │   ├── CreatePlanForm.jsx   # Form for creating plans
│   │   ├── PlansList.jsx    # List and search plans
│   │   └── PlanDetailModal.jsx  # Plan details modal
│   ├── services/
│   │   └── api.js           # API client
│   ├── styles/
│   │   └── index.css        # Global styles
│   └── main.jsx             # React entry point
├── index.html               # Vite HTML template
├── vite.config.js           # Vite configuration
└── package.json             # Dependencies
```

## Key Features

- **Component-based architecture**: Clean separation of concerns
- **Real-time polling**: Automatic status updates for async tasks
- **Professional design**: Clean white theme with blue accents
- **Fast HMR**: Instant updates during development
- **Optimized builds**: Production-ready minified bundles
