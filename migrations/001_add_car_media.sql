-- Migration: Add car_media table for storing car images and videos
-- Created: 2025-11-11
-- Description: Adds support for storing multiple media items (images, videos, documents) per car

-- Create media type enum
CREATE TYPE media_type AS ENUM (
    'image',
    'video',
    'document',
    'three_sixty_view',
    'thumbnail'
);

-- Create storage provider enum
CREATE TYPE storage_provider AS ENUM (
    'cloudinary',
    's3',
    'local',
    'supabase'
);

-- Create car_media table
CREATE TABLE IF NOT EXISTS public.car_media (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    car_id bigint NOT NULL,
    customer_id uuid NOT NULL,
    
    -- Media details
    media_type media_type NOT NULL DEFAULT 'image',
    url text NOT NULL,
    storage_provider storage_provider DEFAULT 'cloudinary',
    file_name varchar(255),
    mime_type varchar(100),
    file_size_bytes bigint,
    
    -- Image-specific metadata
    width integer,
    height integer,
    alt_text text,
    
    -- Ordering and flags
    display_order integer NOT NULL DEFAULT 0,
    is_primary boolean DEFAULT false,
    is_active boolean DEFAULT true,
    
    -- Timestamps
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    
    -- Constraints
    CONSTRAINT car_media_car_id_fkey 
        FOREIGN KEY (car_id) 
        REFERENCES public.cars(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT car_media_customer_id_fkey 
        FOREIGN KEY (customer_id) 
        REFERENCES public.customers(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT car_media_file_size_check 
        CHECK (file_size_bytes >= 0),
    
    CONSTRAINT car_media_display_order_check 
        CHECK (display_order >= 0),
    
    CONSTRAINT car_media_dimensions_check 
        CHECK (
            (media_type = 'image' AND width > 0 AND height > 0) OR
            (media_type != 'image')
        )
);

-- Create unique constraint for primary images (only one primary per car)
CREATE UNIQUE INDEX idx_car_media_one_primary_per_car 
    ON public.car_media(car_id, is_primary) 
    WHERE is_primary = true;

-- Indexes for performance
CREATE INDEX idx_car_media_car_id ON public.car_media(car_id);
CREATE INDEX idx_car_media_customer_id ON public.car_media(customer_id);
CREATE INDEX idx_car_media_type ON public.car_media(media_type);
CREATE INDEX idx_car_media_active ON public.car_media(is_active) WHERE is_active = true;
CREATE INDEX idx_car_media_primary ON public.car_media(car_id, is_primary) WHERE is_primary = true;
CREATE INDEX idx_car_media_display_order ON public.car_media(car_id, display_order);

-- Composite index for common query pattern
CREATE INDEX idx_car_media_lookup 
    ON public.car_media(car_id, media_type, is_active, display_order);

-- Trigger to update updated_at
CREATE OR REPLACE FUNCTION update_car_media_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_car_media_updated_at
    BEFORE UPDATE ON public.car_media
    FOR EACH ROW
    EXECUTE FUNCTION update_car_media_updated_at();

-- Comments for documentation
COMMENT ON TABLE public.car_media IS 'Stores all media (images, videos, documents) associated with cars';
COMMENT ON COLUMN public.car_media.display_order IS 'Order in which media should be displayed (0 = first)';
COMMENT ON COLUMN public.car_media.is_primary IS 'Indicates if this is the main/featured media for the car';
COMMENT ON COLUMN public.car_media.storage_provider IS 'Where the media is stored (cloudinary, s3, etc.)';
COMMENT ON COLUMN public.car_media.alt_text IS 'Alternative text for accessibility and SEO';

-- Row Level Security
ALTER TABLE public.car_media ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "car_media_select_policy" 
    ON public.car_media 
    FOR SELECT 
    USING (
        customer_id = current_setting('app.current_customer_id', true)::uuid
    );

CREATE POLICY "car_media_insert_policy" 
    ON public.car_media 
    FOR INSERT 
    WITH CHECK (
        customer_id = current_setting('app.current_customer_id', true)::uuid
        AND car_id IN (
            SELECT id FROM public.cars WHERE customer_id = current_setting('app.current_customer_id', true)::uuid
        )
    );

CREATE POLICY "car_media_update_policy" 
    ON public.car_media 
    FOR UPDATE 
    USING (
        customer_id = current_setting('app.current_customer_id', true)::uuid
    );

CREATE POLICY "car_media_delete_policy" 
    ON public.car_media 
    FOR DELETE 
    USING (
        customer_id = current_setting('app.current_customer_id', true)::uuid
    );

-- Grants
GRANT ALL ON TABLE public.car_media TO postgres;
GRANT ALL ON TABLE public.car_media TO anon;
GRANT ALL ON TABLE public.car_media TO authenticated;
GRANT ALL ON TABLE public.car_media TO service_role;

-- Grant usage on enums
GRANT USAGE ON TYPE media_type TO postgres;
GRANT USAGE ON TYPE media_type TO anon;
GRANT USAGE ON TYPE media_type TO authenticated;
GRANT USAGE ON TYPE media_type TO service_role;

GRANT USAGE ON TYPE storage_provider TO postgres;
GRANT USAGE ON TYPE storage_provider TO anon;
GRANT USAGE ON TYPE storage_provider TO authenticated;
GRANT USAGE ON TYPE storage_provider TO service_role;

-- Enhanced semantic search function that includes media
CREATE OR REPLACE FUNCTION public.semantic_search_cars_with_images(
    query_embedding public.vector,
    target_customer_id text,
    similarity_threshold double precision DEFAULT 0.7,
    match_limit integer DEFAULT 10
)
RETURNS TABLE(
    id bigint,
    customer_id uuid,
    make text,
    model text,
    model_year integer,
    registration_number text,
    chassis_number text,
    fuel_type text,
    transmission text,
    is_hybrid boolean,
    is_electric boolean,
    seating_capacity integer,
    price_usd numeric,
    mileage_km integer,
    description text,
    features jsonb,
    production_country text,
    owners_count integer,
    created_at timestamp with time zone,
    description_embedding public.vector,
    embedding_model character varying,
    embedding_updated_at timestamp with time zone,
    search_metadata jsonb,
    similarity double precision,
    primary_image_url text,
    image_count bigint
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.customer_id,
        c.make,
        c.model,
        c.model_year,
        c.registration_number,
        c.chassis_number,
        c.fuel_type,
        c.transmission,
        c.is_hybrid,
        c.is_electric,
        c.seating_capacity,
        c.price_usd,
        c.mileage_km,
        c.description,
        c.features,
        c.production_country,
        c.owners_count,
        c.created_at,
        c.description_embedding,
        c.embedding_model,
        c.embedding_updated_at,
        c.search_metadata,
        (1 - (c.description_embedding <=> query_embedding)) as similarity,
        (
            SELECT cm.url 
            FROM car_media cm 
            WHERE cm.car_id = c.id 
                AND cm.is_primary = true 
                AND cm.is_active = true 
            LIMIT 1
        ) as primary_image_url,
        (
            SELECT COUNT(*) 
            FROM car_media cm 
            WHERE cm.car_id = c.id 
                AND cm.media_type = 'image' 
                AND cm.is_active = true
        ) as image_count
    FROM cars c
    WHERE 
        c.customer_id = target_customer_id::uuid
        AND c.description_embedding IS NOT NULL
        AND (1 - (c.description_embedding <=> query_embedding)) >= similarity_threshold
    ORDER BY c.description_embedding <=> query_embedding
    LIMIT match_limit;
END;
$$;

ALTER FUNCTION public.semantic_search_cars_with_images(
    public.vector, 
    text, 
    double precision, 
    integer
) OWNER TO postgres;

GRANT EXECUTE ON FUNCTION public.semantic_search_cars_with_images(
    public.vector, 
    text, 
    double precision, 
    integer
) TO postgres;
GRANT EXECUTE ON FUNCTION public.semantic_search_cars_with_images(
    public.vector, 
    text, 
    double precision, 
    integer
) TO anon;
GRANT EXECUTE ON FUNCTION public.semantic_search_cars_with_images(
    public.vector, 
    text, 
    double precision, 
    integer
) TO authenticated;
GRANT EXECUTE ON FUNCTION public.semantic_search_cars_with_images(
    public.vector, 
    text, 
    double precision, 
    integer
) TO service_role;

COMMENT ON FUNCTION public.semantic_search_cars_with_images IS 'Enhanced semantic search that includes primary image URL and image count for each car';
