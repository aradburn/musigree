/** @jsxImportSource react */
import React, { useEffect, useRef } from "react";

interface AdvertProps {
    adClient: string;
    adSlot: string;
}

// Extend Window interface to include adsbygoogle
declare global {
    interface Window {
        adsbygoogle: unknown[];
    }
}

/**
 * Advert component provides a panel display for small adverts.
 */
export const Advert: React.FC<AdvertProps> = ({ adClient, adSlot }) => {
    const adRef = useRef<HTMLModElement>(null);
    const adStyle = {
        display: "inline-block",
        width: "300px",
        height: "250px",
    };
    const hrStyle = {
        width: "95%",
        height: "2px",
        color: "#000",
        background: "#000",
        opacity: 0.7,
        margin: "auto",
    };

    useEffect(() => {
        const options = {
            // childList: true,
            // characterData: true,
            // characterDataOldValue: true,
            attributes: true,
            // subtree: true,
        };

        // Debug
        const callback = (mutationsList: MutationRecord[]): void => {
            mutationsList.forEach((element) => {
                console.log("Ad: ", element);
            });
        };

        // Check when the adsense ad is loaded
        const obs = new MutationObserver(callback);

        // Use ref to advert
        if (adRef.current) {
            obs.observe(adRef.current, options);
        }

        // Load the advert
        try {
            (window.adsbygoogle = window.adsbygoogle || []).push({});
        } catch (error) {
            console.warn("Failed to load advertisement:", error);
        }

        return (): void => obs.disconnect();
    }, []);

    return (
        <div className="mx-auto">
            <hr className="d-none" style={hrStyle} />
            <h6 className="text-center text-secondary d-none">Advertisment</h6>
            {/* Advert panel */}
            {/* <Image src="/public/img/small-ad.png" rounded /> */}

            {/*  Musigree 300x250 Block Advert  */}
            <ins
                className="adsbygoogle"
                ref={adRef}
                style={adStyle}
                data-ad-client={adClient}
                data-ad-slot={adSlot}
            ></ins>
        </div>
    );
};

export default Advert;
