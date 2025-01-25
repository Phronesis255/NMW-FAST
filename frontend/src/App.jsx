// src/App.jsx
import React, { useState, useRef } from 'react';
import HomePage from './components/HomePage';
import SearchForm from './components/SearchForm';
import GenerateArticle from './components/GenerateArticle';
import AnalysisResults from './components/AnalysisResults';
import EditorComponent from './components/EditorComponent';
import Loading from './components/Loading';
import SeoScale from './components/SeoScale';
import HeadingAnalysis from './components/HeadingAnalysis'; // [ADDED]
import axios from 'axios';

// ------------------------------------------
// Calculate term metrics (unchanged from old)
// ------------------------------------------
const calculateTermMetrics = (tfidfTerms, targetScores, wordCount) => {
  return tfidfTerms.map((term) => {
    const avgTfScore = targetScores[term] || 0;
    const rawTarget = avgTfScore * wordCount;

    const target = Math.floor(rawTarget);
    const delta = Math.max(1, Math.floor(target * 0.1));
    const minOccurrences = Math.max(1, target - delta);
    const maxOccurrences = target + delta;

    return {
      term,
      target,
      delta,
      minOccurrences,
      maxOccurrences,
    };
  });
};

const App = () => {
  // ------------------
  // State and Refs
  // ------------------
  const [page, setPage] = useState('home'); // 'home', 'generate', 'optimize'
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Toggles for Editor, SEO @ Scale, and Heading Analysis screens
  const [showEditor, setShowEditor] = useState(false);
  const [showSeoScale, setShowSeoScale] = useState(false);
  const [showHeadingsAnalysis, setShowHeadingsAnalysis] = useState(false); // [ADDED]
  const [headingData, setHeadingData] = useState([]); // [ADDED]

  // Ref to hold the editor content
  const editorContent = useRef('');

  // --------------------------------------
  // 1) Handle Page Selection from HomePage
  // --------------------------------------
  const handleSelect = (selection) => {
    // selection should be 'generate' or 'optimize'
    setPage(selection);
    setResults(null);
    setShowEditor(false);
    setShowSeoScale(false);
    setShowHeadingsAnalysis(false);
  };

  // --------------------------------------
  // 2) Handle Search (Optimize Page)
  // --------------------------------------
  const handleSearch = async (keyword) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setShowEditor(false);
    setShowSeoScale(false);
    setShowHeadingsAnalysis(false); // [ADDED]

    try {
      console.log('[DEBUG] Fetching analysis results...');
      const response = await axios.post('http://localhost:8000/api/analyze', { keyword });
      setResults(response.data);
      console.log('[DEBUG] Results fetched successfully:', response.data);
    } catch (err) {
      console.error('[DEBUG] API Error:', err);
      setError(err.message || 'An error occurred during the analysis.');
    } finally {
      setLoading(false);
    }
  };

  // --------------------------------------
  // 3) Editor Change Handler
  // --------------------------------------
  const handleEditorChange = (data) => {
    editorContent.current = data;
    console.log('[DEBUG] Updated editor content:', data);
  };

  // --------------------------------------
  // 4) Toggle Editor
  // --------------------------------------
  const toggleEditor = () => {
    setShowEditor((prev) => !prev);
    setShowHeadingsAnalysis(false); // [ADDED]
  };

  // --------------------------------------
  // 5) SEO @ Scale Handlers
  // --------------------------------------
  const handleSeoScale = () => {
    // Show the SEO @ Scale screen
    setShowSeoScale(true);
    setShowEditor(false);
    setShowHeadingsAnalysis(false); // [ADDED]
  };

  const handleBackFromSeoScale = () => {
    // Hide SEO @ Scale screen
    setShowSeoScale(false);
  };

  // --------------------------------------
  // 6) Handle Heading Analysis Navigation [ADDED]
  // --------------------------------------
  const handleGoToHeadingsAnalysis = (headings) => {
    setHeadingData(headings);
    setShowHeadingsAnalysis(true);
    setShowEditor(false); // Ensure Editor is hidden
    setShowSeoScale(false); // Ensure SEO @ Scale is hidden
  };

  const handleBackFromHeadingsAnalysis = () => {
    setShowHeadingsAnalysis(false);
  };

  // --------------------------------------
  // 7) Pre-calculate TF/TF-IDF metrics to pass to Editor
  // --------------------------------------
  const tfidfTerms = results?.tfidf_terms?.map((termObj) => termObj.word) || [];
  const targetScores = results?.tfidf_terms?.reduce((acc, termObj) => {
    acc[termObj.word] = termObj.tf_score || 0;
    return acc;
  }, {}) || {};

  // Count words in Editor
  const wordCount = editorContent.current.split(/\s+/).filter(Boolean).length || 1;
  // Calculate term metrics
  const termsMetrics = calculateTermMetrics(tfidfTerms, targetScores, wordCount);
  console.log('[DEBUG] Calculated Term Metrics:', termsMetrics);

  // --------------------------------------
  // 8) Render
  // --------------------------------------
  return (
    <div className="container mx-auto p-12">

      {/* ------------------------------ Home Page ------------------------------ */}
      {page === 'home' && <HomePage onSelect={handleSelect} />}

      {/* --------------------------- Generate Article Page --------------------------- */}
      {page === 'generate' && (
        <GenerateArticle onBack={() => setPage('home')} />
      )}

      {/* ------------------------------ Optimize Page ------------------------------ */}
      {page === 'optimize' && (
        <>
          {/* If showing SEO @ SCALE screen */}
          {showSeoScale && <SeoScale onBack={handleBackFromSeoScale} />}

          {/* If showing Heading Analysis screen */}
          {showHeadingsAnalysis && (
            <HeadingAnalysis headings={headingData} onBack={handleBackFromHeadingsAnalysis} />
          )}

          {/* If not showing SEO @ SCALE and not showing Heading Analysis and not showing Editor */}
          {!showSeoScale && !showHeadingsAnalysis && !showEditor && (
            <>
              <SearchForm onSearch={handleSearch} onSeoScale={handleSeoScale} />
              {loading && <Loading />}
              {error && <div className="text-red-500 mt-4">Error: {error}</div>}

              {results && (
                <>
                  <AnalysisResults results={results} onGoToEditor={toggleEditor} onGoToHeadingsAnalysis={handleGoToHeadingsAnalysis}/>


                  {/* Button to toggle Editor */}
                  <button onClick={toggleEditor} className="btn btn-primary mt-6">
                    Go to Editor
                  </button>
                </>
              )}
            </>
          )}

          {/* If showing Editor and not showing SEO @ SCALE and not showing Heading Analysis */}
          {!showSeoScale && !showHeadingsAnalysis && showEditor && (
            <>
              <EditorComponent
                tfidfTerms={tfidfTerms}
                targetScores={targetScores}
                onChange={handleEditorChange}
              />
              <div className="flex justify-between mt-6">
                <button onClick={toggleEditor} className="btn btn-secondary">
                  Back to Analysis
                </button>
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
};

export default App;
