import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Send, Image, Calendar, Hash, AtSign, Loader2 } from 'lucide-react';
import clsx from 'clsx';

const SUPPORTED_PLATFORMS = [
  { id: 'twitter', name: 'Twitter', color: 'bg-blue-500' },
  { id: 'facebook', name: 'Facebook', color: 'bg-blue-600' },
  { id: 'instagram', name: 'Instagram', color: 'bg-pink-500' },
  { id: 'linkedin', name: 'LinkedIn', color: 'bg-blue-700' },
  { id: 'bluesky', name: 'Bluesky', color: 'bg-sky-500' },
  { id: 'pinterest', name: 'Pinterest', color: 'bg-red-500' },
  { id: 'tiktok', name: 'TikTok', color: 'bg-black' },
];

const PostForm = ({ onSubmit, isLoading }) => {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [mediaUrls, setMediaUrls] = useState(['']);
  const [hashtags, setHashtags] = useState(['']);
  const [mentions, setMentions] = useState(['']);

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
    reset,
  } = useForm({
    defaultValues: {
      post: '',
      platforms: [],
      randomPost: false,
      randomMediaUrl: false,
      isPortraitVideo: false,
      isLandscapeVideo: false,
      scheduleDate: '',
    },
  });

  const watchedValues = watch();

  const handleFormSubmit = (data) => {
    // Process media URLs
    const validMediaUrls = mediaUrls.filter(url => url.trim() !== '');
    
    // Process hashtags
    const validHashtags = hashtags.filter(tag => tag.trim() !== '');
    
    // Process mentions
    const validMentions = mentions.filter(mention => mention.trim() !== '');

    const postData = {
      ...data,
      mediaUrls: validMediaUrls.length > 0 ? validMediaUrls : undefined,
      hashtags: validHashtags.length > 0 ? validHashtags : undefined,
      mentions: validMentions.length > 0 ? validMentions : undefined,
      scheduleDate: data.scheduleDate ? new Date(data.scheduleDate).toISOString() : undefined,
    };

    onSubmit(postData);
  };

  const addMediaUrl = () => {
    setMediaUrls([...mediaUrls, '']);
  };

  const removeMediaUrl = (index) => {
    setMediaUrls(mediaUrls.filter((_, i) => i !== index));
  };

  const updateMediaUrl = (index, value) => {
    const newUrls = [...mediaUrls];
    newUrls[index] = value;
    setMediaUrls(newUrls);
  };

  const addHashtag = () => {
    setHashtags([...hashtags, '']);
  };

  const removeHashtag = (index) => {
    setHashtags(hashtags.filter((_, i) => i !== index));
  };

  const updateHashtag = (index, value) => {
    const newTags = [...hashtags];
    newTags[index] = value.startsWith('#') ? value : `#${value}`;
    setHashtags(newTags);
  };

  const addMention = () => {
    setMentions([...mentions, '']);
  };

  const removeMention = (index) => {
    setMentions(mentions.filter((_, i) => i !== index));
  };

  const updateMention = (index, value) => {
    const newMentions = [...mentions];
    newMentions[index] = value.startsWith('@') ? value : `@${value}`;
    setMentions(newMentions);
  };

  const resetForm = () => {
    reset();
    setMediaUrls(['']);
    setHashtags(['']);
    setMentions(['']);
    setShowAdvanced(false);
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Create Social Media Post</h2>
        <button
          type="button"
          onClick={resetForm}
          className="btn btn-secondary text-sm"
        >
          Reset Form
        </button>
      </div>

      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
        {/* Post Content */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Post Content
          </label>
          <textarea
            {...register('post', {
              required: !watchedValues.randomPost ? 'Post content is required' : false,
              maxLength: { value: 2200, message: 'Post content is too long' },
            })}
            className={clsx('textarea h-32', {
              'border-red-500': errors.post,
            })}
            placeholder="What would you like to share?"
            disabled={watchedValues.randomPost}
          />
          {errors.post && (
            <p className="mt-1 text-sm text-red-600">{errors.post.message}</p>
          )}
          <div className="mt-1 flex items-center justify-between text-sm text-gray-500">
            <span>
              {watchedValues.post?.length || 0} / 2200 characters
            </span>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                {...register('randomPost')}
                className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <span>Use random test content</span>
            </label>
          </div>
        </div>

        {/* Platform Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Select Platforms
          </label>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {SUPPORTED_PLATFORMS.map((platform) => (
              <label
                key={platform.id}
                className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
              >
                <input
                  type="checkbox"
                  value={platform.id}
                  {...register('platforms', {
                    required: 'Please select at least one platform',
                  })}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <div className={clsx('w-3 h-3 rounded-full', platform.color)} />
                <span className="text-sm font-medium text-gray-700">
                  {platform.name}
                </span>
              </label>
            ))}
          </div>
          {errors.platforms && (
            <p className="mt-1 text-sm text-red-600">{errors.platforms.message}</p>
          )}
        </div>

        {/* Advanced Options Toggle */}
        <div>
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center space-x-2 text-primary-600 hover:text-primary-700 font-medium"
          >
            <span>{showAdvanced ? 'Hide' : 'Show'} Advanced Options</span>
            <svg
              className={clsx('w-4 h-4 transition-transform', {
                'rotate-180': showAdvanced,
              })}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        {/* Advanced Options */}
        {showAdvanced && (
          <div className="space-y-6 p-4 bg-gray-50 rounded-lg">
            {/* Media URLs */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium text-gray-700">
                  <Image className="w-4 h-4 inline mr-2" />
                  Media URLs
                </label>
                <div className="flex items-center space-x-2">
                  <label className="flex items-center space-x-2 text-sm">
                    <input
                      type="checkbox"
                      {...register('randomMediaUrl')}
                      className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span>Use random test media</span>
                  </label>
                </div>
              </div>
              {!watchedValues.randomMediaUrl && (
                <div className="space-y-2">
                  {mediaUrls.map((url, index) => (
                    <div key={index} className="flex items-center space-x-2">
                      <input
                        type="url"
                        value={url}
                        onChange={(e) => updateMediaUrl(index, e.target.value)}
                        className="input flex-1"
                        placeholder="https://example.com/image.jpg"
                      />
                      {mediaUrls.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeMediaUrl(index)}
                          className="text-red-600 hover:text-red-700"
                        >
                          ✕
                        </button>
                      )}
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={addMediaUrl}
                    className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                  >
                    + Add Media URL
                  </button>
                </div>
              )}
            </div>

            {/* Video Format Options */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Video Format (if using video)
              </label>
              <div className="flex space-x-4">
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    value="landscape"
                    {...register('videoFormat')}
                    onChange={() => {
                      setValue('isLandscapeVideo', true);
                      setValue('isPortraitVideo', false);
                    }}
                    className="text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm">Landscape</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="radio"
                    value="portrait"
                    {...register('videoFormat')}
                    onChange={() => {
                      setValue('isPortraitVideo', true);
                      setValue('isLandscapeVideo', false);
                    }}
                    className="text-primary-600 focus:ring-primary-500"
                  />
                  <span className="text-sm">Portrait (TikTok/Reels)</span>
                </label>
              </div>
            </div>

            {/* Hashtags */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium text-gray-700">
                  <Hash className="w-4 h-4 inline mr-2" />
                  Hashtags
                </label>
              </div>
              <div className="space-y-2">
                {hashtags.map((tag, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={tag}
                      onChange={(e) => updateHashtag(index, e.target.value)}
                      className="input flex-1"
                      placeholder="#hashtag"
                    />
                    {hashtags.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeHashtag(index)}
                        className="text-red-600 hover:text-red-700"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  onClick={addHashtag}
                  className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                >
                  + Add Hashtag
                </button>
              </div>
            </div>

            {/* Mentions */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <label className="block text-sm font-medium text-gray-700">
                  <AtSign className="w-4 h-4 inline mr-2" />
                  Mentions
                </label>
              </div>
              <div className="space-y-2">
                {mentions.map((mention, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={mention}
                      onChange={(e) => updateMention(index, e.target.value)}
                      className="input flex-1"
                      placeholder="@username"
                    />
                    {mentions.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeMention(index)}
                        className="text-red-600 hover:text-red-700"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
                <button
                  type="button"
                  onClick={addMention}
                  className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                >
                  + Add Mention
                </button>
              </div>
            </div>

            {/* Schedule Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-2" />
                Schedule Post (Optional)
              </label>
              <input
                type="datetime-local"
                {...register('scheduleDate')}
                className="input"
                min={new Date().toISOString().slice(0, 16)}
              />
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="flex items-center justify-between pt-6 border-t border-gray-200">
          <div className="text-sm text-gray-500">
            {watchedValues.platforms?.length > 0 && (
              <span>
                Posting to {watchedValues.platforms.length} platform
                {watchedValues.platforms.length !== 1 ? 's' : ''}
              </span>
            )}
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className={clsx('btn btn-primary flex items-center space-x-2', {
              'btn-disabled': isLoading,
            })}
          >
            {isLoading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span>{isLoading ? 'Posting...' : 'Create Post'}</span>
          </button>
        </div>
      </form>
    </div>
  );
};

export default PostForm;