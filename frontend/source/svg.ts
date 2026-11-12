/**
 * @fileoverview SVG manipulation utilities for Musigree
 * This module provides functionality for SVG initialization, sizing, definition setup,
 * and SVG export capabilities. It handles SVG element manipulation, styling, and
 * conversion to other image formats.
 */

import * as d3 from "d3";
import {musigreeManager} from "./core/singletons";
import {DOM_IDS, GRADIENT, MARKER, SVG, SVG_IDS} from "./constants";
import {convertRemToPixels} from "./utils";

/** Fixed desktop sidebar widths, in rem. The canvas uses whatever is left. */
const SIDEBAR_LEFT_REM = 20;
const SIDEBAR_RIGHT_REM = 30;
const SIDEBAR_RIGHT_COLLAPSED_REM = 5;

/** Stroke thickness as a fraction of the shorter viewBox side. */
const INITIAL_CANVAS_PATH_STROKE_WIDTH_RATIO = 0.0025;
const INITIAL_CANVAS_PATH_STROKE = "#333";

/** The logo artwork is authored in this viewBox. */
const INITIAL_CANVAS_LOGO_WIDTH = 1048;
const INITIAL_CANVAS_LOGO_HEIGHT = 469;
/** Logo width as a fraction of the canvas viewBox width. */
const INITIAL_CANVAS_LOGO_WIDTH_RATIO = 2 / 3;

/**
 * True when the page was opened with a non-empty query string.
 * An empty search (`""` or `"?"`) is treated as no parameters.
 */
const hasUrlQueryParameters = (): boolean => {
    return new URLSearchParams(window.location.search).toString().length > 0;
};

/**
 * The Musigree logo, in its own 1048×469 viewBox.
 */
const INITIAL_CANVAS_LOGO_PATH = `M 110.00,101.00
           C 116.31,99.21 131.69,99.99 139.00,100.00
             142.41,100.01 145.84,99.81 148.96,101.45
             155.52,104.90 157.69,117.23 159.72,124.00
             159.72,124.00 182.00,191.00 182.00,191.00
             182.00,191.00 192.33,160.00 192.33,160.00
             192.33,160.00 204.33,122.00 204.33,122.00
             206.20,116.40 208.99,104.23 214.10,101.31
             216.77,99.79 220.03,100.01 223.00,100.00
             223.00,100.00 249.00,100.00 249.00,100.00
             247.09,105.98 244.03,105.84 241.09,111.00
             238.86,114.91 239.01,118.68 239.00,123.00
             239.00,123.00 239.00,189.00 239.00,189.00
             239.00,189.00 238.32,232.00 238.32,232.00
             237.98,236.58 239.47,245.09 241.99,248.96
             244.84,253.34 246.92,252.52 249.00,258.00
             249.00,258.00 230.00,260.16 230.00,260.16
             230.00,260.16 203.00,263.00 203.00,263.00
             203.00,263.00 213.25,247.00 213.25,247.00
             213.25,247.00 216.00,224.00 216.00,224.00
             216.00,224.00 216.00,180.00 216.00,180.00
             216.00,180.00 215.00,148.00 215.00,148.00
             215.00,148.00 205.00,179.00 205.00,179.00
             205.00,179.00 189.33,227.00 189.33,227.00
             187.73,231.80 185.01,241.05 182.52,244.98
             181.33,246.88 179.06,250.10 176.40,248.83
             174.42,247.89 173.33,243.96 172.67,242.00
             172.67,242.00 166.58,223.00 166.58,223.00
             166.58,223.00 154.34,186.00 154.34,186.00
             154.34,186.00 142.00,150.00 142.00,150.00
             142.00,150.00 142.00,242.00 142.00,242.00
             142.01,249.39 142.55,254.33 148.10,259.90
             151.93,263.74 153.96,263.42 158.00,268.00
             158.00,268.00 124.00,276.11 124.00,276.11
             118.81,277.31 114.36,279.80 110.00,276.11
             121.48,267.30 123.83,257.91 124.00,244.00
             124.00,244.00 124.00,127.00 124.00,127.00
             123.98,114.37 121.98,108.88 110.00,103.00
             110.00,103.00 110.00,101.00 110.00,101.00 Z
           M 372.23,251.00
           C 370.05,244.15 371.11,220.40 372.23,213.00
             373.07,209.64 375.66,201.46 380.68,204.13
             384.07,205.93 381.67,210.81 382.18,216.00
             382.86,223.05 386.27,229.06 392.00,233.21
             410.17,246.39 428.06,234.57 426.90,218.00
             425.94,204.09 411.11,195.80 401.00,188.57
             401.00,188.57 387.17,177.83 387.17,177.83
             375.36,166.11 370.59,147.86 376.10,132.00
             378.16,126.09 382.11,120.55 387.01,116.68
             392.96,111.99 398.67,110.47 406.00,109.43
             418.03,107.71 432.12,114.05 437.00,114.03
             438.86,114.02 441.14,113.35 443.00,113.00
             443.00,113.00 445.00,147.00 445.00,147.00
             444.96,149.07 444.96,154.24 441.34,152.60
             439.02,151.55 436.47,145.36 435.22,143.00
             431.02,135.10 424.83,125.56 415.00,125.04
             400.90,124.31 392.58,137.53 398.41,150.00
             406.93,168.22 436.93,176.50 446.68,197.00
             453.84,212.07 451.10,234.57 437.99,245.67
             430.78,251.78 421.24,254.16 412.00,254.82
             401.27,255.58 387.79,249.92 378.00,246.00
             375.93,249.41 375.76,249.64 372.23,251.00 Z
           M 618.00,179.00
           C 608.85,183.96 609.78,188.00 608.58,197.00
             608.58,197.00 607.97,243.00 607.97,243.00
             607.97,243.00 607.97,246.98 607.97,246.98
             607.05,256.94 601.82,246.58 593.00,248.76
             593.00,248.76 581.00,252.33 581.00,252.33
             567.20,255.33 552.03,252.97 541.00,243.68
             532.06,236.14 526.63,225.19 523.90,214.00
             521.56,204.42 520.95,192.85 521.00,183.00
             521.00,183.00 521.91,172.00 521.91,172.00
             523.49,149.46 528.82,126.73 550.00,114.46
             560.26,108.53 572.77,108.63 584.00,111.23
             584.00,111.23 597.00,114.92 597.00,114.92
             597.00,114.92 606.00,113.00 606.00,113.00
             606.00,113.00 607.19,139.00 607.19,139.00
             607.19,139.00 607.19,147.00 607.19,147.00
             607.67,151.02 605.73,154.95 601.63,151.40
             599.79,149.80 595.68,141.68 593.90,139.00
             586.88,128.43 576.24,120.03 564.01,128.80
             556.90,133.90 553.55,142.88 551.29,151.00
             547.20,165.76 546.95,191.79 549.13,207.00
             550.29,215.08 552.63,224.75 558.21,230.97
             564.62,238.09 578.63,241.35 583.98,230.97
             585.19,228.63 584.99,225.59 585.00,223.00
             585.02,213.93 586.44,196.65 582.33,189.01
             578.54,181.97 574.51,183.65 571.00,177.00
             571.00,177.00 595.00,176.00 595.00,176.00
             595.00,176.00 618.00,177.00 618.00,177.00
             618.00,177.00 618.00,179.00 618.00,179.00 Z
           M 262.00,114.00
           C 262.00,114.00 281.00,112.96 281.00,112.96
             281.00,112.96 296.00,112.96 296.00,112.96
             296.00,112.96 305.00,112.00 305.00,112.00
             303.07,117.50 300.19,115.93 296.85,120.21
             293.83,124.08 294.01,128.39 294.00,133.00
             294.00,133.00 294.00,215.00 294.00,215.00
             294.02,225.89 297.96,238.06 311.00,238.73
             323.77,239.38 329.86,228.17 330.05,217.00
             330.05,217.00 330.05,204.00 330.05,204.00
             330.05,204.00 331.00,190.00 331.00,190.00
             331.00,190.00 331.00,147.00 331.00,147.00
             331.00,147.00 330.00,134.00 330.00,134.00
             329.96,130.00 330.43,125.70 328.55,122.01
             326.67,118.34 324.30,117.49 322.00,113.00
             322.00,113.00 360.00,113.00 360.00,113.00
             357.95,118.94 353.40,118.34 351.42,125.00
             349.55,131.26 350.00,144.09 350.00,151.00
             350.00,151.00 350.00,197.00 350.00,197.00
             350.00,197.00 351.00,210.00 351.00,210.00
             351.11,219.52 350.24,230.87 344.89,239.00
             341.50,244.16 335.66,248.98 330.00,251.47
             318.65,256.47 296.56,256.83 286.00,249.89
             273.75,241.84 269.02,230.18 269.00,216.00
             269.00,216.00 269.00,150.00 269.00,150.00
             269.00,144.47 269.57,127.20 268.15,123.00
             266.93,119.41 264.33,116.87 262.00,114.00 Z
           M 464.00,113.00
           C 464.00,113.00 483.00,112.00 483.00,112.00
             483.00,112.00 507.00,113.00 507.00,113.00
             507.00,113.00 507.00,115.00 507.00,115.00
             504.45,116.49 502.53,117.46 500.85,120.05
             496.93,126.13 498.00,144.29 498.00,152.00
             498.00,152.00 498.00,229.00 498.00,229.00
             498.01,233.36 497.98,238.05 500.14,242.00
             502.66,246.59 505.20,246.37 507.00,251.99
             507.00,251.99 473.00,251.99 473.00,251.99
             473.00,251.99 470.02,251.99 470.02,251.99
             459.28,251.55 469.88,245.34 471.91,241.96
             473.79,238.83 473.95,235.53 474.00,232.00
             474.00,232.00 474.00,151.00 474.00,151.00
             474.00,143.70 475.17,125.78 471.72,120.09
             469.88,117.04 466.66,115.25 464.00,113.00 Z
           M 626.00,113.00
           C 633.67,110.82 637.52,112.91 645.00,113.00
             645.00,113.00 670.00,113.00 670.00,113.00
             684.12,113.00 698.94,112.32 709.91,123.10
             720.21,133.23 719.06,143.95 719.00,157.00
             718.93,171.27 710.75,186.39 696.00,190.00
             696.00,190.00 707.32,219.00 707.32,219.00
             709.60,225.18 712.55,233.93 716.68,238.91
             720.29,243.26 724.24,245.25 729.00,248.00
             728.03,249.72 727.90,250.53 725.86,251.40
             723.54,252.39 708.52,252.04 705.00,252.00
             692.33,251.83 691.66,244.94 687.42,235.00
             687.42,235.00 671.00,195.00 671.00,195.00
             671.00,195.00 661.00,196.00 661.00,196.00
             661.00,196.00 661.00,233.00 661.00,233.00
             661.06,237.68 661.20,240.11 664.26,243.91
             665.47,245.42 669.13,248.23 667.83,250.44
             666.78,252.23 662.80,251.99 661.00,252.00
             653.28,252.05 633.34,252.80 627.00,251.00
             629.47,246.19 631.80,245.82 634.27,241.99
             636.89,237.92 636.99,231.71 637.00,227.00
             637.00,227.00 637.00,163.00 637.00,163.00
             637.00,163.00 637.00,136.00 637.00,136.00
             636.99,131.82 637.07,127.88 635.23,124.00
             633.14,119.57 629.06,116.71 626.00,113.00 Z
           M 739.00,112.00
           C 739.00,112.00 790.00,113.00 790.00,113.00
             790.00,113.00 819.00,112.00 819.00,112.00
             822.60,121.83 823.00,135.52 823.00,146.00
             813.34,144.42 815.71,136.67 803.00,130.90
             795.66,127.57 792.18,128.52 785.00,127.80
             782.25,127.21 777.77,126.39 775.31,127.80
             772.95,129.60 773.05,132.48 773.00,135.00
             773.00,135.00 773.00,175.00 773.00,175.00
             782.53,172.68 788.03,176.59 795.63,167.96
             797.02,166.38 799.74,161.63 802.42,163.17
             804.09,164.12 803.97,167.35 804.06,169.00
             804.06,169.00 804.06,196.00 804.06,196.00
             804.19,197.76 804.61,201.41 801.87,201.39
             798.38,201.37 798.20,195.79 792.00,192.01
             786.66,188.75 779.04,189.00 773.00,189.00
             773.00,189.00 773.00,238.00 773.00,238.00
             783.65,238.00 797.54,239.31 807.00,234.10
             819.19,227.38 817.48,219.46 826.00,218.00
             825.99,227.60 824.44,234.76 822.13,244.00
             821.49,246.54 820.67,251.43 818.49,252.98
             816.73,254.23 813.13,254.00 811.00,254.00
             811.00,254.00 762.00,253.00 762.00,253.00
             762.00,253.00 749.00,252.01 749.00,252.01
             746.88,251.96 742.17,252.24 740.41,251.43
             738.96,250.76 738.84,250.12 738.00,249.00
             749.17,242.52 747.32,236.17 748.09,225.00
             748.09,225.00 749.00,215.00 749.00,215.00
             749.00,215.00 749.00,157.00 749.00,157.00
             749.00,149.78 748.73,129.05 746.66,123.00
             744.84,117.68 741.78,117.41 739.00,112.00 Z
           M 837.00,113.00
           C 837.00,113.00 867.00,112.00 867.00,112.00
             867.00,112.00 926.00,112.00 926.00,112.00
             926.03,121.24 929.11,141.58 927.00,149.00
             919.71,146.23 920.46,139.52 910.00,132.47
             899.83,125.61 886.68,127.00 875.00,127.00
             875.00,127.00 875.00,175.00 875.00,175.00
             881.97,175.00 893.10,176.02 898.67,171.35
             900.84,169.53 902.53,166.42 904.00,164.00
             908.11,165.65 907.92,166.74 908.00,171.00
             908.00,171.00 908.00,196.00 908.00,196.00
             907.96,197.80 907.87,203.67 904.44,201.83
             902.21,200.64 901.58,195.79 896.96,192.74
             892.10,189.53 880.84,190.00 875.00,190.00
             875.00,190.00 876.00,241.00 876.00,241.00
             887.74,241.00 902.74,242.38 913.00,235.87
             918.45,232.41 920.52,229.23 923.92,224.06
             924.96,222.47 926.43,220.02 928.74,220.74
             932.33,221.87 930.04,231.20 929.57,234.00
             929.57,234.00 926.34,251.00 926.34,251.00
             925.88,253.08 925.22,256.66 923.44,257.98
             921.69,259.27 917.18,259.04 915.00,258.99
             915.00,258.99 906.00,258.09 906.00,258.09
             906.00,258.09 885.00,257.00 885.00,257.00
             885.00,257.00 868.00,256.00 868.00,256.00
             868.00,256.00 839.00,254.00 839.00,254.00
             839.00,254.00 839.00,252.00 839.00,252.00
             848.16,245.00 848.98,239.00 849.00,228.00
             849.00,228.00 849.00,159.00 849.00,159.00
             849.00,150.85 849.81,131.85 847.11,125.00
             845.21,120.17 840.28,116.98 837.00,113.00 Z
           M 661.00,180.00
           C 668.79,180.00 678.36,180.20 684.96,175.35
             696.07,167.20 697.26,141.63 686.82,132.53
             679.92,126.52 669.55,127.00 661.00,127.00
             661.00,127.00 661.00,180.00 661.00,180.00 Z
           M 494.00,292.14
           C 494.00,292.14 543.00,292.14 543.00,292.14
             543.00,292.14 601.00,292.14 601.00,292.14
             601.00,292.14 617.00,293.00 617.00,293.00
             617.00,293.00 644.00,293.00 644.00,293.00
             644.00,293.00 659.00,294.00 659.00,294.00
             659.00,294.00 704.00,294.00 704.00,294.00
             704.00,294.00 719.00,295.00 719.00,295.00
             719.00,295.00 750.00,296.00 750.00,296.00
             750.00,296.00 771.00,297.00 771.00,297.00
             771.00,297.00 786.00,298.00 786.00,298.00
             786.00,298.00 829.00,300.00 829.00,300.00
             829.00,300.00 844.00,301.00 844.00,301.00
             858.42,301.17 885.49,302.68 893.86,316.00
             904.34,332.69 887.27,353.48 869.00,346.74
             858.67,342.93 857.40,330.19 865.01,327.79
             871.62,325.72 870.18,334.56 875.11,336.72
             880.35,339.01 887.78,330.33 883.26,323.00
             878.01,314.48 868.14,312.65 859.00,311.92
             859.00,311.92 840.00,311.00 840.00,311.00
             840.00,311.00 825.00,310.00 825.00,310.00
             825.00,310.00 799.00,309.00 799.00,309.00
             799.00,309.00 786.00,308.00 786.00,308.00
             786.00,308.00 757.00,307.00 757.00,307.00
             757.00,307.00 742.00,306.00 742.00,306.00
             742.00,306.00 721.00,305.00 721.00,305.00
             721.00,305.00 701.00,305.00 701.00,305.00
             701.00,305.00 680.00,304.00 680.00,304.00
             680.00,304.00 639.00,304.00 639.00,304.00
             639.00,304.00 624.00,303.00 624.00,303.00
             624.00,303.00 601.00,303.00 601.00,303.00
             601.00,303.00 584.00,302.00 584.00,302.00
             584.00,302.00 478.00,302.00 478.00,302.00
             478.00,302.00 461.00,303.00 461.00,303.00
             461.00,303.00 423.00,303.00 423.00,303.00
             423.00,303.00 407.00,304.00 407.00,304.00
             407.00,304.00 391.00,304.00 391.00,304.00
             391.00,304.00 375.00,305.00 375.00,305.00
             375.00,305.00 347.00,305.00 347.00,305.00
             347.00,305.00 332.00,306.00 332.00,306.00
             332.00,306.00 319.00,306.00 319.00,306.00
             319.00,306.00 303.00,307.04 303.00,307.04
             303.00,307.04 291.00,307.04 291.00,307.04
             291.00,307.04 279.00,308.00 279.00,308.00
             279.00,308.00 227.00,310.00 227.00,310.00
             227.00,310.00 215.00,310.96 215.00,310.96
             215.00,310.96 205.00,310.96 205.00,310.96
             205.00,310.96 195.00,311.91 195.00,311.91
             187.61,312.42 182.32,311.96 175.00,314.93
             170.70,316.67 165.36,320.49 163.75,325.00
             161.69,330.78 166.88,337.16 171.00,337.26
             177.21,337.40 175.96,329.06 180.14,327.66
             185.44,325.88 191.75,334.34 183.78,342.89
             173.95,353.44 150.10,346.49 151.04,325.00
             151.64,311.23 164.34,306.04 176.00,303.80
             186.70,301.75 218.44,300.02 230.00,300.00
             230.00,300.00 266.00,298.00 266.00,298.00
             266.00,298.00 285.00,297.00 285.00,297.00
             285.00,297.00 313.00,296.00 313.00,296.00
             313.00,296.00 327.00,295.00 327.00,295.00
             327.00,295.00 344.00,295.00 344.00,295.00
             344.00,295.00 360.00,294.00 360.00,294.00
             360.00,294.00 395.00,294.00 395.00,294.00
             395.00,294.00 412.00,293.00 412.00,293.00
             412.00,293.00 464.00,293.00 464.00,293.00
             464.00,293.00 494.00,292.14 494.00,292.14 Z`;

/**
 * Places the logo in the middle of the canvas.
 * Width is one third of the viewport; height follows the logo aspect ratio.
 * Scale is applied first, then the translation that centers the scaled viewBox.
 */
const initialCanvasLogoTransform = (
    viewportWidth: number,
    viewportHeight: number,
): string => {
    const scale =
        (viewportWidth * INITIAL_CANVAS_LOGO_WIDTH_RATIO) /
        INITIAL_CANVAS_LOGO_WIDTH;
    const scaledHeight = INITIAL_CANVAS_LOGO_HEIGHT * scale;
    const translateX =
        (viewportWidth - viewportWidth * INITIAL_CANVAS_LOGO_WIDTH_RATIO) / 2;
    const translateY = (viewportHeight - scaledHeight) / 2;
    return `translate(${translateX}, ${translateY}) scale(${scale})`;
};

/**
 * Initializes the SVG element with basic setup
 * - Sets up window dimensions
 * - Creates SVG definitions (markers, gradients)
 */
export const initSvg = (): void => {
    const svgContainer = document.getElementById(DOM_IDS.SVG_CONTAINER);
    if (!svgContainer) {
        console.error("SVG container not found");
        return;
    }

    // Get the SVG element
    const svgElement = document.getElementById(DOM_IDS.SVG);
    if (svgElement) {
        console.debug("SVG element already exists");
        return;
    }

    const svgSelection = d3.select(DOM_IDS.SVG_CONTAINER_ID);

    // Create the SVG canvas
    // Create the SVG element if it doesn't exist yet
    //                 if (!document.getElementById(DOM_IDS.SVG)) {
    //                     const svg = document.createElementNS(
    //                         "http://www.w3.org/2000/svg",
    //                         "svg",
    //                     );
    //                     svg.id = DOM_IDS.SVG;
    //                     containerRef.current.appendChild(svg);
    //                 }
    svgSelection.append("svg").attr("id", DOM_IDS.SVG);

    // Setup window dimensions on SVG element
    setSvgSize(DOM_IDS.SVG_ID);

    // Setup SVG common definitions
    setupSvgDefs(DOM_IDS.SVG_ID);

    // Home visits with no query have nothing to draw until a network loads.
    drawInitialCanvasPath();
};

/**
 * Draws the logo on the canvas when the URL has no query parameters.
 * Gives the empty home view a path to render until a network replaces it.
 */
export const drawInitialCanvasPath = (): void => {
    if (hasUrlQueryParameters()) {
        return;
    }
    if (document.getElementById(SVG_IDS.INITIAL_CANVAS_PATH)) {
        return;
    }

    const svgSelection = d3.select(DOM_IDS.SVG_ID);
    if (svgSelection.empty()) {
        return;
    }

    const [svgWidth, svgHeight] = musigreeManager.svgDimensions;
    if (!(svgWidth > 0) || !(svgHeight > 0)) {
        return;
    }

    const scale =
        (svgWidth * INITIAL_CANVAS_LOGO_WIDTH_RATIO) /
        INITIAL_CANVAS_LOGO_WIDTH;
    // Stroke is in the logo's local space, and the transform scales it.
    const strokeWidth =
        (Math.min(svgWidth, svgHeight) *
            INITIAL_CANVAS_PATH_STROKE_WIDTH_RATIO) /
        scale;

    svgSelection
        .append("path")
        .attr("id", SVG_IDS.INITIAL_CANVAS_PATH)
        .attr("class", "initial-canvas-path")
        .attr("d", INITIAL_CANVAS_LOGO_PATH)
        .attr("transform", initialCanvasLogoTransform(svgWidth, svgHeight))
        .attr("fill", "none")
        .attr("stroke", INITIAL_CANVAS_PATH_STROKE)
        .attr("stroke-width", String(strokeWidth))
        .attr("stroke-linecap", "round");
};

/**
 * Removes the startup logo so a loaded network owns the canvas.
 */
export const removeInitialCanvasPath = (): void => {
    d3.select(`#${SVG_IDS.INITIAL_CANVAS_PATH}`).remove();
};

/**
 * Sets the size and viewport attributes of the main SVG element
 * Uses global musigreeManager.dimensions and musigreeManager.svgDimensions for sizing
 */
export const setSvgSize = (svgSelector: string): void => {
    try {
        const dpr = window.devicePixelRatio || 1;
        console.log("window devicePixelRatio: ", dpr);

        const svgContainer = document.getElementById(DOM_IDS.SVG_CONTAINER);
        const navTopContainer = document.getElementById(DOM_IDS.NAV_TOP);

        // Add null check to prevent errors when the SVG container doesn't exist
        if (!svgContainer) {
            console.error(
                `SVG container element with ID "${DOM_IDS.SVG_CONTAINER}" not found. Skipping window initialization.`,
            );
            return;
        }

        // Prefer the laid-out canvas. Before that exists, reserve the fixed sidebars.
        const navHeight = navTopContainer?.clientHeight ?? 0;
        const isDesktop = window.innerWidth >= 576;
        const sidebarRem = musigreeManager.isSidebarRightCollapsed
            ? SIDEBAR_LEFT_REM + SIDEBAR_RIGHT_COLLAPSED_REM
            : SIDEBAR_LEFT_REM + SIDEBAR_RIGHT_REM;
        const fallbackWidth = isDesktop
            ? Math.max(0, window.innerWidth - convertRemToPixels(sidebarRem))
            : window.innerWidth;
        const width =
            svgContainer.clientWidth > 0
                ? svgContainer.clientWidth
                : fallbackWidth;
        // Desktop height is the viewport below the top nav. The container can
        // still report the SVG's intrinsic 150px before that layout exists.
        const height = isDesktop
            ? Math.max(0, window.innerHeight - navHeight)
            : Math.max(0, (window.innerHeight - navHeight) / 2.0);
        const svgContainerDimensions: [number, number] = [width, height];
        const svgCanvasDimensions: [number, number] = [
            svgContainerDimensions[0] * SVG.VIEWPORT_SIZE_MULTIPLIER * dpr,
            svgContainerDimensions[1] * SVG.VIEWPORT_SIZE_MULTIPLIER * dpr,
        ];
        console.log("svgContainerDimensions: ", svgContainerDimensions);
        console.log("svgCanvasDimensions: ", svgCanvasDimensions);

        musigreeManager.dpr = dpr;
        musigreeManager.dimensions = svgContainerDimensions;
        musigreeManager.svgDimensions = svgCanvasDimensions;

        //         const [width, height] = musigreeManager.dimensions;
        const [svgWidth, svgHeight] = musigreeManager.svgDimensions;

        // Get the SVG element
        const svgSelection = d3.select(svgSelector);

        // Check if we have a valid selection before setting attributes
        if (svgSelection.empty()) {
            console.warn("SVG element or attr function not found");
            return;
        }

        console.log("Set SVG dim: ", width, height);
        console.log("Set SVG size: ", svgWidth, svgHeight);

        // Setup window dimensions on SVG element
        svgSelection
            .attr("width", String(width))
            .attr("height", String(height))
            .attr("viewBox", `0 0 ${svgWidth} ${svgHeight}`)
            .attr("preserveAspectRatio", "none");
    } catch (err) {
        console.error("Error setting SVG size:", err);
    }
};

/**
 * Sets up SVG definitions including:
 * - Arrowhead marker for directed connections
 * - Aggregate marker for relationship indicators
 * - Radial gradient for visual effects
 */
export const setupSvgDefs = (svgSelector: string): void => {
    try {
        // Get the SVG element
        const svgSelection = d3.select(svgSelector);

        // Check if we have a valid selection before setting attributes
        if (svgSelection.empty()) {
            console.warn("SVG element or append function not found");
            return;
        }

        const defs = svgSelection.append("defs");

        // ARROWHEAD
        defs.append("marker")
            .attr("id", SVG_IDS.ARROWHEAD)
            .attr("viewBox", MARKER.VIEWBOX)
            .attr("refX", MARKER.ARROWHEAD_REFX)
            .attr("refY", MARKER.REFY)
            .attr("markerWidth", MARKER.WIDTH)
            .attr("markerHeight", MARKER.HEIGHT)
            .attr("markerUnits", "strokeWidth")
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M 0,0 m -5,-5 L 5,0 L -5,5 L -2.5,0 L -5,-5 Z")
            .attr("stroke-linecap", "round")
            .attr("stroke-linejoin", "round");

        // AGGREGATE
        defs.append("marker")
            .attr("id", SVG_IDS.AGGREGATE)
            .attr("viewBox", MARKER.VIEWBOX)
            .attr("refX", MARKER.AGGREGATE_REFX)
            .attr("refY", MARKER.REFY)
            .attr("markerWidth", MARKER.WIDTH)
            .attr("markerHeight", MARKER.HEIGHT)
            .attr("markerUnits", "strokeWidth")
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M 0,0 m 5,0 L 0,-3 L -5,0 L 0,3 L 5,0 Z")
            .attr("fill", "#fff")
            .attr("stroke", "#000")
            .attr("stroke-linecap", "round")
            .attr("stroke-linejoin", "round")
            .attr("stroke-width", MARKER.STROKE_WIDTH);

        // RADIAL GRADIENT
        const gradient = defs
            .append("radialGradient")
            .attr("id", SVG_IDS.RADIAL_GRADIENT);

        GRADIENT.STOPS.forEach(({offset, opacity}) => {
            gradient
                .append("stop")
                .attr("offset", offset)
                .attr("stop-color", GRADIENT.COLOR)
                .attr("stop-opacity", opacity);
        });
    } catch (err) {
        console.error("Error setting up SVG definitions:", err);
    }
};
