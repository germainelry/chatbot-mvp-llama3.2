import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { MessageSquare, BarChart3, Users, BookOpen } from 'lucide-react';
import CustomerChat from './pages/CustomerChat';
import AgentDashboard from './pages/AgentDashboard';
import Analytics from './pages/Analytics';
import KnowledgeBase from './pages/KnowledgeBase';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <MessageSquare className="h-8 w-8 text-primary-600" />
                  <span className="ml-2 text-xl font-bold text-gray-900">
                    AI Support Assistant
                  </span>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  <Link
                    to="/customer"
                    className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700"
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    Customer Chat
                  </Link>
                  <Link
                    to="/agent"
                    className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700"
                  >
                    <Users className="h-4 w-4 mr-2" />
                    Agent Dashboard
                  </Link>
                  <Link
                    to="/analytics"
                    className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700"
                  >
                    <BarChart3 className="h-4 w-4 mr-2" />
                    Analytics
                  </Link>
                  <Link
                    to="/knowledge-base"
                    className="inline-flex items-center px-1 pt-1 border-b-2 border-transparent text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700"
                  >
                    <BookOpen className="h-4 w-4 mr-2" />
                    Knowledge Base
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main>
          <Routes>
            <Route path="/" element={<CustomerChat />} />
            <Route path="/customer" element={<CustomerChat />} />
            <Route path="/agent" element={<AgentDashboard />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/knowledge-base" element={<KnowledgeBase />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;

