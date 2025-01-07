// src/components/DrawerSidebar.jsx
import React from 'react';
import GenerateArticle from './GenerateArticle';

const DrawerSidebar = ({ open, onClose }) => {
    return (
        <div className={`drawer ${open ? 'drawer-open' : ''}`}>
            <input id="my-drawer" type="checkbox" className="drawer-toggle" checked={open} readOnly />
            <div className="drawer-content">
                {/* Page content here */}
                <label htmlFor="my-drawer" className="btn btn-primary" onClick={onClose}>Close</label>
            </div>
            <div className="drawer-side">
                <label htmlFor="my-drawer" className="drawer-overlay" onClick={onClose}></label>
                <div className="menu p-4 w-80 bg-base-100 text-base-content">
                    <GenerateArticle />
                </div>
            </div>
        </div>
    );
};

export default DrawerSidebar;