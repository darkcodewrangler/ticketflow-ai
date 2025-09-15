# TicketFlow AI - Frontend

A modern, AI-powered customer support ticket management system built with React, TypeScript, and Vite. This frontend application provides an intuitive interface for managing support tickets with intelligent automation and real-time processing capabilities.

## 📋 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Development](#-development)
- [Building](#-building)
- [Deployment](#-deployment)
- [Project Structure](#-project-structure)
- [API Integration](#-api-integration)
- [Contributing](#-contributing)
- [License](#-license)

## ✨ Features

### Core Functionality

- **Intelligent Ticket Management**: Create, view, and manage support tickets with AI-powered categorization
- **Real-time Processing**: Live updates via WebSocket connections for ticket status changes
- **AI Agent Integration**: Automated ticket resolution with confidence scoring and escalation
- **Advanced Analytics**: Comprehensive dashboard with metrics and performance insights
- **Knowledge Base**: Searchable repository of solutions and documentation

### User Interface

- **Modern Design**: Clean, responsive interface built with Tailwind CSS and shadcn/ui
- **Dark/Light Theme**: Automatic theme switching with system preference detection
- **Mobile Responsive**: Optimized for desktop, tablet, and mobile devices
- **Accessibility**: WCAG compliant with keyboard navigation and screen reader support

### Advanced Features

- **Live Processing View**: Real-time workflow visualization and step-by-step processing
- **Smart Search**: Intelligent search across tickets, knowledge base, and solutions
- **Integration Hub**: Connect with Slack, email systems, and webhooks
- **Customizable Settings**: Comprehensive configuration for agents, notifications, and integrations
- **Activity Feed**: Real-time updates on system activities and ticket changes

## 🛠 Tech Stack

### Core Technologies

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe development with full IntelliSense support
- **Vite** - Fast build tool and development server
- **React Router DOM** - Client-side routing and navigation

### UI Framework & Styling

- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - High-quality, accessible React components
- **Radix UI** - Unstyled, accessible UI primitives
- **Lucide React** - Beautiful, customizable icons

### State Management & Data Fetching

- **TanStack Query** - Powerful data synchronization for React
- **React Hook Form** - Performant, flexible forms with easy validation
- **Zod** - TypeScript-first schema validation

### Charts & Visualization

- **Recharts** - Composable charting library for React
- **React Resizable Panels** - Flexible panel layouts

### Development Tools

- **ESLint** - Code linting and quality enforcement
- **TypeScript ESLint** - TypeScript-specific linting rules
- **PostCSS** - CSS processing and optimization
- **Autoprefixer** - Automatic CSS vendor prefixing

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Node.js** (version 18.0 or higher)
- **pnpm** (recommended) or npm/yarn
- **Git** for version control

## 🚀 Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd ticketflow-ai/frontend
   ```

2. **Install dependencies**

   ```bash
   pnpm install
   ```

3. **Set up environment variables**

   ```bash
   cp .env.example .env.local
   ```

   Configure the following variables in `.env.local`:

   ```env
   VITE_API_BASE_URL=http://localhost:8000
   VITE_WS_URL=ws://localhost:8000/ws
   ```

## 💻 Development

### Start the development server

```bash
pnpm dev
```

The application will be available at `http://localhost:5173`

### Available Scripts

- `pnpm dev` - Start development server with hot reload
- `pnpm build` - Build for production
- `pnpm build:dev` - Build in development mode
- `pnpm preview` - Preview production build locally
- `pnpm lint` - Run ESLint for code quality checks

### Development Features

- **Hot Module Replacement (HMR)** - Instant updates during development
- **TypeScript Support** - Full type checking and IntelliSense
- **Auto-formatting** - Consistent code style with ESLint
- **Component Tagging** - Development-time component identification

## 🏗 Building

### Production Build

```bash
pnpm build
```

This creates an optimized production build in the `dist/` directory with:

- Minified and compressed assets
- Tree-shaken JavaScript bundles
- Optimized CSS with unused styles removed
- Static asset optimization

### Development Build

```bash
pnpm build:dev
```

Creates a development build with source maps and debugging information.

### Preview Production Build

```bash
pnpm preview
```

Serves the production build locally for testing before deployment.

## 🚀 Deployment

### Vercel (Recommended)

The project is configured for seamless Vercel deployment:

1. **Connect your repository** to Vercel
2. **Configure environment variables** in Vercel dashboard
3. **Deploy** - Vercel will automatically build and deploy

The `vercel.json` configuration handles SPA routing:

```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

### Other Platforms

#### Netlify

1. Build command: `pnpm build`
2. Publish directory: `dist`
3. Add `_redirects` file: `/* /index.html 200`

#### Traditional Hosting

1. Run `pnpm build`
2. Upload `dist/` contents to your web server
3. Configure server to serve `index.html` for all routes

### Environment Variables for Production

Set these environment variables in your deployment platform:

```env
VITE_API_BASE_URL=https://your-api-domain.com
VITE_WS_URL=wss://your-api-domain.com/ws
```

## 📁 Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── ui/             # shadcn/ui components
│   ├── layout/         # Layout components (Header, Sidebar, etc.)
│   ├── charts/         # Chart components
│   └── settings/       # Settings-specific components
├── contexts/           # React contexts for state management
├── hooks/              # Custom React hooks
├── lib/                # Utility libraries and configurations
├── pages/              # Page components (routes)
├── services/           # API services and external integrations
├── types/              # TypeScript type definitions
└── utils/              # Utility functions
```

### Key Directories

- **`components/`** - Modular, reusable React components
- **`pages/`** - Top-level route components
- **`types/`** - Comprehensive TypeScript interfaces
- **`services/`** - API integration and data fetching
- **`contexts/`** - Global state management
- **`hooks/`** - Custom hooks for shared logic

## 🔌 API Integration

The frontend integrates with the TicketFlow AI backend through:

### REST API

- **Base URL**: Configured via `VITE_API_BASE_URL`
- **Endpoints**: Defined in `src/services/api.ts`
- **Authentication**: Token-based authentication
- **Error Handling**: Centralized error management

### WebSocket Connection

- **Real-time Updates**: Live ticket status changes
- **Connection Management**: Automatic reconnection
- **Message Types**: Ticket updates, metrics, agent status

### Key API Features

- Ticket CRUD operations
- AI agent workflow management
- Analytics and metrics
- Knowledge base search
- Integration management

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests and linting**
   ```bash
   pnpm lint
   pnpm build
   ```
5. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
6. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Development Guidelines

- Follow TypeScript best practices
- Use existing component patterns
- Maintain responsive design principles
- Add proper error handling
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🆘 Support

For support and questions:

- **Documentation**: Check the inline code documentation
- **Issues**: Create an issue in the repository
- **Discussions**: Use GitHub Discussions for questions

## 🔄 Updates

Stay updated with the latest changes:

- Watch the repository for notifications
- Check the changelog for version updates
- Follow the project roadmap for upcoming features
