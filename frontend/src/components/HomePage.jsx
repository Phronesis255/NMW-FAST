import React from 'react';

const HomePage = ({ onSelect }) => {
    return (
        <div className="flex justify-center items-center h-screen">
            <div className="card w-96 bg-base-100 shadow-xl m-4 cursor-pointer" onClick={() => onSelect('generate')}>
                <div className="card-body">
                    <h2 className="card-title">Generate a New Article</h2>
                    <p>Create a new article from scratch.</p>
                </div>
            </div>
            <div className="card w-96 bg-base-100 shadow-xl m-4 cursor-pointer" onClick={() => onSelect('optimize')}>
                <div className="card-body">
                    <h2 className="card-title">Optimize Existing Article</h2>
                    <p>Optimize an existing article for SEO.</p>
                </div>
            </div>
        </div>
    );
};

export default HomePage;