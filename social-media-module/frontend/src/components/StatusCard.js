import React from 'react';
import { CheckCircle, XCircle, AlertCircle, Loader2, Wifi, WifiOff } from 'lucide-react';
import clsx from 'clsx';

const StatusCard = ({ healthStatus, isLoading, onRefresh }) => {
  const getStatusIcon = () => {
    if (isLoading) {
      return <Loader2 className="w-5 h-5 animate-spin text-blue-500" />;
    }
    
    if (!healthStatus) {
      return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
    
    if (healthStatus.status === 'healthy' && healthStatus.ayrshare_connected) {
      return <CheckCircle className="w-5 h-5 text-success-500" />;
    }
    
    return <XCircle className="w-5 h-5 text-error-500" />;
  };

  const getStatusText = () => {
    if (isLoading) return 'Checking status...';
    if (!healthStatus) return 'Status unknown';
    
    if (healthStatus.status === 'healthy' && healthStatus.ayrshare_connected) {
      return 'All systems operational';
    }
    
    if (healthStatus.status === 'healthy' && !healthStatus.ayrshare_connected) {
      return 'API healthy, Ayrshare disconnected';
    }
    
    return 'System issues detected';
  };

  const getStatusColor = () => {
    if (isLoading) return 'border-blue-200 bg-blue-50';
    if (!healthStatus) return 'border-yellow-200 bg-yellow-50';
    
    if (healthStatus.status === 'healthy' && healthStatus.ayrshare_connected) {
      return 'border-success-200 bg-success-50';
    }
    
    return 'border-error-200 bg-error-50';
  };

  return (
    <div className={clsx('card border-l-4', getStatusColor())}>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          {getStatusIcon()}
          <div>
            <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
            <p className="text-sm text-gray-600">{getStatusText()}</p>
          </div>
        </div>
        <button
          onClick={onRefresh}
          disabled={isLoading}
          className={clsx('btn btn-secondary text-sm', {
            'btn-disabled': isLoading,
          })}
        >
          {isLoading ? 'Checking...' : 'Refresh'}
        </button>
      </div>

      {healthStatus && (
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              {healthStatus.status === 'healthy' ? (
                <CheckCircle className="w-4 h-4 text-success-500" />
              ) : (
                <XCircle className="w-4 h-4 text-error-500" />
              )}
              <span className="text-sm font-medium text-gray-700">API Status</span>
            </div>
            <span className={clsx('badge', {
              'badge-success': healthStatus.status === 'healthy',
              'badge-error': healthStatus.status !== 'healthy',
            })}>
              {healthStatus.status}
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1">
              {healthStatus.ayrshare_connected ? (
                <Wifi className="w-4 h-4 text-success-500" />
              ) : (
                <WifiOff className="w-4 h-4 text-error-500" />
              )}
              <span className="text-sm font-medium text-gray-700">Ayrshare</span>
            </div>
            <span className={clsx('badge', {
              'badge-success': healthStatus.ayrshare_connected,
              'badge-error': !healthStatus.ayrshare_connected,
            })}>
              {healthStatus.ayrshare_connected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      )}

      {healthStatus && healthStatus.timestamp && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <p className="text-xs text-gray-500">
            Last checked: {new Date(healthStatus.timestamp).toLocaleString()}
          </p>
        </div>
      )}

      {healthStatus && !healthStatus.ayrshare_connected && (
        <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>Note:</strong> Ayrshare API is not connected. Please check your API key configuration.
          </p>
        </div>
      )}
    </div>
  );
};

export default StatusCard;