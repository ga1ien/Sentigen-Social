import React, { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { Share2, Settings, BarChart3, Users } from 'lucide-react';
import PostForm from './components/PostForm';
import PostResult from './components/PostResult';
import StatusCard from './components/StatusCard';
import { useSocialMedia } from './hooks/useSocialMedia';

function App() {
  const [activeTab, setActiveTab] = useState('post');
  const [postResult, setPostResult] = useState(null);
  
  const {
    isLoading,
    healthStatus,
    connectedAccounts,
    createPost,
    checkHealth,
  } = useSocialMedia();

  const handleCreatePost = async (postData) => {
    try {
      const result = await createPost(postData);
      setPostResult(result);
    } catch (error) {
      console.error('Failed to create post:', error);
    }
  };

  const tabs = [
    { id: 'post', name: 'Create Post', icon: Share2 },
    { id: 'status', name: 'Status', icon: Settings },
    { id: 'accounts', name: 'Accounts', icon: Users },
    { id: 'analytics', name: 'Analytics', icon: BarChart3 },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'post':
        return (
          <PostForm
            onSubmit={handleCreatePost}
            isLoading={isLoading}
          />
        );
      
      case 'status':
        return (
          <StatusCard
            healthStatus={healthStatus}
            isLoading={isLoading}
            onRefresh={checkHealth}
          />
        );
      
      case 'accounts':
        return (
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Connected Accounts</h2>
            {connectedAccounts && connectedAccounts.length > 0 ? (
              <div className="space-y-4">
                {connectedAccounts.map((account, index) => (
                  <div key={index} className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">{account.platform}</h3>
                        <p className="text-sm text-gray-600">{account.username || account.name}</p>
                      </div>
                      <span className="badge badge-success">Connected</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Connected Accounts</h3>
                <p className="text-gray-600 mb-4">
                  Connect your social media accounts in the Ayrshare dashboard to start posting.
                </p>
                <a
                  href="https://app.ayrshare.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-primary"
                >
                  Open Ayrshare Dashboard
                </a>
              </div>
            )}
          </div>
        );
      
      case 'analytics':
        return (
          <div className="card">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Analytics</h2>
            <div className="text-center py-12">
              <BarChart3 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Analytics Coming Soon</h3>
              <p className="text-gray-600">
                Post analytics and performance metrics will be available here.
              </p>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#363636',
            color: '#fff',
          },
          success: {
            duration: 3000,
            iconTheme: {
              primary: '#22c55e',
              secondary: '#fff',
            },
          },
          error: {
            duration: 5000,
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fff',
            },
          },
        }}
      />

      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="flex items-center justify-center w-10 h-10 bg-primary-600 rounded-lg">
                <Share2 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Social Media Module</h1>
                <p className="text-sm text-gray-600">AI-powered social media posting</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  healthStatus?.status === 'healthy' && healthStatus?.ayrshare_connected
                    ? 'bg-success-500'
                    : 'bg-error-500'
                }`} />
                <span className="text-sm text-gray-600">
                  {healthStatus?.status === 'healthy' && healthStatus?.ayrshare_connected
                    ? 'Connected'
                    : 'Disconnected'
                  }
                </span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-fade-in">
          {renderTabContent()}
        </div>
      </main>

      {/* Post Result Modal */}
      {postResult && (
        <PostResult
          result={postResult}
          onClose={() => setPostResult(null)}
        />
      )}

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Social Media Module v1.0.0 - Powered by Ayrshare & Pydantic AI
            </div>
            <div className="flex items-center space-x-6">
              <a
                href="https://docs.ayrshare.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-600 hover:text-primary-600"
              >
                API Documentation
              </a>
              <a
                href="https://app.ayrshare.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-gray-600 hover:text-primary-600"
              >
                Ayrshare Dashboard
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;