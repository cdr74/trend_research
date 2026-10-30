import { useState, useRef, useEffect, useCallback } from "react";

export interface ZoomPanTransform {
  x: number;
  y: number;
  k: number;
}

interface UseZoomPanOptions {
  minZoom?: number;
  maxZoom?: number;
  initialZoom?: number;
}

export function useZoomPan(options: UseZoomPanOptions = {}) {
  const { minZoom = 0.6, maxZoom = 6.0, initialZoom = 1.0 } = options;

  const [transform, setTransform] = useState<ZoomPanTransform>({
    x: 0,
    y: 0,
    k: initialZoom,
  });

  const svgRef = useRef<SVGSVGElement | null>(null);
  const isDraggingRef = useRef(false);
  const hasDraggedRef = useRef(false);
  const dragStartRef = useRef({ mouseX: 0, mouseY: 0, originX: 0, originY: 0 });

  // Native non-passive wheel event listener to prevent page scrolling while zooming
  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl) return;

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const rect = svgEl.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const zoomFactor = e.deltaY < 0 ? 1.15 : 0.87;

      setTransform((prev) => {
        const newK = Math.min(maxZoom, Math.max(minZoom, prev.k * zoomFactor));
        if (newK === prev.k) return prev;

        const ratio = newK / prev.k;
        const newX = mouseX - (mouseX - prev.x) * ratio;
        const newY = mouseY - (mouseY - prev.y) * ratio;

        return { x: newX, y: newY, k: newK };
      });
    };

    svgEl.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      svgEl.removeEventListener("wheel", onWheel);
    };
  }, [minZoom, maxZoom]);

  const onMouseDown = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    // Only drag on primary left mouse button
    if (e.button !== 0) return;
    isDraggingRef.current = true;
    hasDraggedRef.current = false;
    dragStartRef.current = {
      mouseX: e.clientX,
      mouseY: e.clientY,
      originX: transform.x,
      originY: transform.y,
    };
  }, [transform.x, transform.y]);

  const onMouseMove = useCallback((e: React.MouseEvent<SVGSVGElement>) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - dragStartRef.current.mouseX;
    const dy = e.clientY - dragStartRef.current.mouseY;

    if (Math.hypot(dx, dy) > 4) {
      hasDraggedRef.current = true;
    }

    setTransform((prev) => ({
      ...prev,
      x: dragStartRef.current.originX + dx,
      y: dragStartRef.current.originY + dy,
    }));
  }, []);

  const onMouseUp = useCallback(() => {
    isDraggingRef.current = false;
  }, []);

  const onMouseLeave = useCallback(() => {
    isDraggingRef.current = false;
  }, []);

  const zoomAroundCenter = useCallback(
    (factor: number) => {
      const svgEl = svgRef.current;
      if (!svgEl) return;

      const rect = svgEl.getBoundingClientRect();
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      setTransform((prev) => {
        const newK = Math.min(maxZoom, Math.max(minZoom, prev.k * factor));
        if (newK === prev.k) return prev;

        const ratio = newK / prev.k;
        const newX = centerX - (centerX - prev.x) * ratio;
        const newY = centerY - (centerY - prev.y) * ratio;

        return { x: newX, y: newY, k: newK };
      });
    },
    [minZoom, maxZoom]
  );

  const zoomIn = useCallback(() => zoomAroundCenter(1.25), [zoomAroundCenter]);
  const zoomOut = useCallback(() => zoomAroundCenter(0.8), [zoomAroundCenter]);
  const resetZoom = useCallback(() => {
    setTransform({ x: 0, y: 0, k: 1.0 });
  }, []);

  return {
    svgRef,
    transform,
    zoomIn,
    zoomOut,
    resetZoom,
    hasDraggedRef,
    handlers: {
      onMouseDown,
      onMouseMove,
      onMouseUp,
      onMouseLeave,
    },
  };
}
