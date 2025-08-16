import { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';

export const useSocialMedia = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [connectedAccounts, setConnectedAccounts] = useState([]);
  const [healthStatus, setHealthStatus] = useState(null);

  // Load connected accounts on mount
  useEffect(() => {
    loadConnectedAccounts();
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const health = await apiService.healthCheck();
      setHealthStatus(health);
    } catch (error) {
      console.error('Health check failed:', error);
      setHealthStatus({ status: 'unhealthy', ayrshare_connected: false });
    }
  };

  const loadConnectedAccounts = async () => {
    try {
      setIsLoading(true);
      const accounts = await apiService.getConnectedAccounts();
      setConnectedAccounts(accounts);
    } catch (error) {
      console.error('Failed to load connected accounts:', error);
      toast.error('Failed to load connected accounts');
    } finally {
      setIsLoading(false);
    }
  };

  const createPost = async (postData) => {
    try {
      setIsLoading(true);
      const result = await apiService.createPost(postData);
      
      if (result.status === 'success') {
        toast.success('Post created successfully!');
      } else {
        toast.error(result.message || 'Failed to create post');
      }
      
      return result;
    } catch (error) {
      console.error('Failed to create post:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to create post';
      toast.error(errorMessage);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const optimizeContent = async (content, platforms, options = {}) => {
    try {
      setIsLoading(true);
      const result = await apiService.optimizeContent(content, platforms, options);
      return result;
    } catch (error) {
      console.error('Failed to optimize content:', error);
      toast.error('Failed to optimize content');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const getPostAnalytics = async (postId) => {
    try {
      setIsLoading(true);
      const result = await apiService.getPostAnalytics(postId);
      return result;
    } catch (error) {
      console.error('Failed to get analytics:', error);
      toast.error('Failed to get post analytics');
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    isLoading,
    connectedAccounts,
    healthStatus,
    createPost,
    optimizeContent,
    getPostAnalytics,
    loadConnectedAccounts,
    checkHealth,
  };
};