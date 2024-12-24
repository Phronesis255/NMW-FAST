import React, { useState } from 'react';

const SearchForm = ({ onSearch, onSeoScale }) => {
    const [keyword, setKeyword] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        onSearch(keyword);
    };

    return (
        <div className="flex items-center justify-between gap-8 w-full">
            {/* Left: Input and Buttons */}
            <form onSubmit={handleSubmit} className="flex items-center space-x-4">
                <input
                    type="text"
                    value={keyword}
                    onChange={(e) => setKeyword(e.target.value)}
                    placeholder="Enter a keyword"
                    className="input input-bordered w-64"
                />
                <button type="submit" className="btn btn-primary">
                    Start Analysis
                </button>
                <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={onSeoScale}
                >
                    SEO @ SCALE
                </button>
            </form>

            {/* Right: Huge Title */}
            <h1 className="text-5xl font-extrabold text-right">
                Needs More Words
            </h1>
        </div>
    );
};

export default SearchForm;
