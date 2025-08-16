import React from 'react';
import { CheckCircle, XCircle, ExternalLink, Copy, Calendar } from 'lucide-react';
import clsx from 'clsx';
import toast from 'react-hot-toast';

const PostResult = ({ result, onClose }) => {
  if (!result) return null;

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  const formatDate = (dateString) => {
    if (!dateString) return null;
    return new Date(dateString).toLocaleString();
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'success':
        return <span className="badge badge-success">Success</span>;
      case 'error':
        return <span className="badge badge-error">Error</span>;
      case 'pending':
        return <span className="badge badge-warning">Pending</span>;
      default:
        return <span className="badge badge-info">{status}</span>;
    }
  };

  const getPlatformColor = (platform) => {
    const colors = {
      twitter: 'bg-blue-500',
      facebook: 'bg-blue-600',
      instagram: 'bg-pink-500',
      linkedin: 'bg-blue-700',
      bluesky: 'bg-sky-500',
      pinterest: 'bg-red-500',
      tiktok: 'bg-black',
    };
    return colors[platform?.toLowerCase()] || 'bg-gray-500';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center space-x-3">
              {result.status === 'success' ? (
                <CheckCircle className="w-8 h-8 text-success-600" />
              ) : (
                <XCircle className="w-8 h-8 text-error-600" />
              )}
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  Post {result.status === 'success' ? 'Created' : 'Failed'}
                </h2>
                <p className="text-gray-600">{result.message}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
            >
              ×
            </button>
          </div>

          {/* Overall Status */}
          <div className="mb-6">
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">Overall Status</p>
                <p className="text-sm text-gray-600">{result.message}</p>
              </div>
              {getStatusBadge(result.status)}
            </div>
          </div>

          {/* Post Content */}
          {result.post_content && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Post Content</h3>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-gray-800 whitespace-pre-wrap">{result.post_content}</p>
                <button
                  onClick={() => copyToClipboard(result.post_content)}
                  className="mt-2 flex items-center space-x-1 text-primary-600 hover:text-primary-700 text-sm"
                >
                  <Copy className="w-4 h-4" />
                  <span>Copy Content</span>
                </button>
              </div>
            </div>
          )}

          {/* Post IDs */}
          {(result.post_id || result.ref_id) && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Post Information</h3>
              <div className="space-y-2">
                {result.post_id && (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm font-medium text-gray-700">Post ID:</span>
                    <div className="flex items-center space-x-2">
                      <code className="text-sm bg-white px-2 py-1 rounded border">
                        {result.post_id}
                      </code>
                      <button
                        onClick={() => copyToClipboard(result.post_id)}
                        className="text-primary-600 hover:text-primary-700"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
                {result.ref_id && (
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <span className="text-sm font-medium text-gray-700">Reference ID:</span>
                    <div className="flex items-center space-x-2">
                      <code className="text-sm bg-white px-2 py-1 rounded border">
                        {result.ref_id}
                      </code>
                      <button
                        onClick={() => copyToClipboard(result.ref_id)}
                        className="text-primary-600 hover:text-primary-700"
                      >
                        <Copy className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Platform Results */}
          {result.platform_results && result.platform_results.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Platform Results</h3>
              <div className="space-y-3">
                {result.platform_results.map((platformResult, index) => (
                  <div
                    key={index}
                    className={clsx(
                      'p-4 rounded-lg border-l-4',
                      platformResult.status === 'success'
                        ? 'bg-success-50 border-success-500'
                        : 'bg-error-50 border-error-500'
                    )}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <div
                          className={clsx(
                            'w-4 h-4 rounded-full',
                            getPlatformColor(platformResult.platform)
                          )}
                        />
                        <span className="font-medium text-gray-900 capitalize">
                          {platformResult.platform}
                        </span>
                        {getStatusBadge(platformResult.status)}
                      </div>
                      {platformResult.post_url && (
                        <a
                          href={platformResult.post_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center space-x-1 text-primary-600 hover:text-primary-700 text-sm"
                        >
                          <ExternalLink className="w-4 h-4" />
                          <span>View Post</span>
                        </a>
                      )}
                    </div>

                    {platformResult.post_id && (
                      <div className="mb-2">
                        <span className="text-sm text-gray-600">Post ID: </span>
                        <code className="text-sm bg-white px-2 py-1 rounded border">
                          {platformResult.post_id}
                        </code>
                      </div>
                    )}

                    {platformResult.error_message && (
                      <div className="text-sm text-error-700 bg-error-100 p-2 rounded">
                        {platformResult.error_message}
                      </div>
                    )}

                    {platformResult.used_quota && (
                      <div className="text-sm text-gray-600">
                        API Quota Used: {platformResult.used_quota}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Errors */}
          {result.errors && result.errors.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Errors</h3>
              <div className="space-y-2">
                {result.errors.map((error, index) => (
                  <div key={index} className="p-3 bg-error-50 border border-error-200 rounded-lg">
                    <p className="text-error-800 text-sm">{error}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Timestamps */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Timestamps</h3>
            <div className="space-y-2">
              {result.created_at && (
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <Calendar className="w-4 h-4" />
                  <span>Created: {formatDate(result.created_at)}</span>
                </div>
              )}
              {result.scheduled_for && (
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <Calendar className="w-4 h-4" />
                  <span>Scheduled for: {formatDate(result.scheduled_for)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end space-x-3 pt-6 border-t border-gray-200">
            <button
              onClick={onClose}
              className="btn btn-secondary"
            >
              Close
            </button>
            {result.post_id && (
              <button
                onClick={() => {
                  // This would typically navigate to an analytics page
                  toast.success('Analytics feature coming soon!');
                }}
                className="btn btn-primary"
              >
                View Analytics
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PostResult;