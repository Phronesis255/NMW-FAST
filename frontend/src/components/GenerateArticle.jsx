import React, { useEffect, useState } from 'react';
import axios from 'axios';
import SimpleEditorComponent from './SimpleEditorComponent';

const GenerateArticle = ({ onBack }) => {
  const [keyword, setKeyword] = useState('');
  const [title, setTitle] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [editorContent, setEditorContent] = useState(null);

  // Store metrics from the backend
  const [metrics, setMetrics] = useState(null);

  // An array of step messages to cycle through while loading
  const loadingSteps = [
    'Generating outline',
    'Generating sections',
    'Putting it all together',
    'Finalizing article content',
  ];
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  // Cycle through loadingSteps while loading
  useEffect(() => {
    let intervalId;
    if (loading) {
      // Reset to the first step when loading starts
      setCurrentStepIndex(0);

      // Rotate steps every 3 seconds
      intervalId = setInterval(() => {
        setCurrentStepIndex((prevIndex) => (prevIndex + 1) % loadingSteps.length);
      }, 3000);
    }
    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [loading]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    setMetrics(null);
    setEditorContent(null);

    try {
      const response = await axios.post('http://localhost:8000/api/generate-article', {
        keyword,
        title,
      });

      // Parse response
      const { message, content, metrics: returnedMetrics } = response.data;
      setSuccess(message);
      setEditorContent(content);

      // If the server returns metrics, store them
      if (returnedMetrics) {
        setMetrics(returnedMetrics);
      }
    } catch (err) {
      setError(err.message || 'An error occurred during article generation.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto">
      <h2 className="text-4xl font-bold mb-6 text-center">Generate a New Article</h2>

      {/* If the editor content doesn’t exist yet, display the form; otherwise show the editor */}
      {!editorContent ? (
        <div className="card w-full max-w-xl mx-auto shadow-xl bg-base-100">
          <div className="card-body">
            <form onSubmit={handleSubmit} className="form-control gap-4">
              <div className="form-control">
                <label className="label">
                  <span className="label-text font-semibold">Keyword</span>
                </label>
                <input
                  type="text"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  className="input input-bordered"
                  placeholder="Enter a keyword"
                  required
                />
              </div>

              <div className="form-control">
                <label className="label">
                  <span className="label-text font-semibold">Title</span>
                </label>
                <input
                  type="text"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="input input-bordered"
                  placeholder="Enter an article title"
                  required
                />
              </div>

              {/* Error & Success messages */}
              {error && (
                <div className="alert alert-error shadow-lg mt-2">
                  <span>{error}</span>
                </div>
              )}
              {success && (
                <div className="alert alert-success shadow-lg mt-2">
                  <span>{success}</span>
                </div>
              )}

              <div className="mt-4 flex gap-2">
                <button type="submit" className="btn btn-primary" disabled={loading}>
                  {loading ? 'Generating...' : 'Submit'}
                </button>
                <button type="button" className="btn btn-accent" onClick={onBack}>
                  Back
                </button>
              </div>
            </form>

            {/* Show loading spinner and rotating steps if loading */}
            {loading && (
              <div className="flex flex-col items-center justify-center mt-6 space-y-4">
                {/* DaisyUI loading spinner */}
                <span className="loading loading-spinner loading-lg text-primary" />
                <p className="text-lg font-semibold">
                  {loadingSteps[currentStepIndex]}
                </p>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="card w-full max-w-5xl mx-auto shadow-xl bg-base-100">
          <div className="card-body">
            <SimpleEditorComponent initialContent={editorContent} />

            {/* If metrics exist, display them as DaisyUI badges */}
            {metrics && (
              <div className="flex flex-wrap gap-2 mt-6">
                {metrics.final_blog_post_length !== undefined && (
                  <div className="badge badge-outline">
                    Length: {metrics.final_blog_post_length}
                  </div>
                )}
                {metrics.total_generation_time !== undefined && (
                  <div className="badge badge-secondary">
                    Time: {metrics.total_generation_time.toFixed(2)} s
                  </div>
                )}
                {metrics.model_name && (
                  <div className="badge badge-ghost">
                    Model: {metrics.model_name}
                  </div>
                )}
                {metrics.similarity_to_title !== undefined && (
                  <div className="badge badge-info">
                    Similarity: {metrics.similarity_to_title.toFixed(2)}%
                  </div>
                )}
                {metrics.reading_difficulty_grade !== undefined && (
                  <div className="badge badge-accent">
                    Reading Grade: {metrics.reading_difficulty_grade.toFixed(2)}
                  </div>
                )}
                {metrics.keyword_density !== undefined && (
                  <div className="badge badge-primary">
                    Keyword Density: {metrics.keyword_density.toFixed(2)}%
                  </div>
                )}
                {metrics.gunning_fog !== undefined && (
                  <div className="badge badge-outline">
                    Gunning Fog: {metrics.gunning_fog.toFixed(2)}
                  </div>
                )}
              </div>
            )}

            <div className="mt-6">
              <button className="btn btn-accent" onClick={onBack}>
                Back
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default GenerateArticle;
