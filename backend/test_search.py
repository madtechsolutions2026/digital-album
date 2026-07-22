"""
Test face search with different thresholds to find optimal value.
"""
import asyncio
import numpy as np
from sqlalchemy import select
from app.database import async_session_maker
from app.models import Photo, FaceEmbedding, Event

async def test_search():
    async with async_session_maker() as db:
        # Get all embeddings
        result = await db.execute(
            select(FaceEmbedding, Photo, Event)
            .select_from(FaceEmbedding)
            .join(Photo, FaceEmbedding.photo_id == Photo.photo_id)
            .join(Event, Photo.event_id == Event.event_id)
        )
        all_embeddings = result.all()
        
        print("=" * 60)
        print(f"FOUND {len(all_embeddings)} FACE EMBEDDINGS")
        print("=" * 60)
        
        if len(all_embeddings) < 2:
            print("\n⚠️  Need at least 2 embeddings to test search")
            return
        
        # Take first embedding as "query"
        query_emb, query_photo, query_event = all_embeddings[0]
        query_vector = np.array(query_emb.embedding_vector)
        
        print(f"\nUsing as query: Photo {query_photo.photo_id} from event '{query_event.name}'")
        print(f"Bounding box: {query_emb.bounding_box}")
        print(f"Confidence: {query_emb.confidence_score:.3f}")
        
        print("\n" + "=" * 60)
        print("SIMILARITY SCORES TO ALL OTHER FACES:")
        print("=" * 60)
        
        # Calculate similarity to all others
        similarities = []
        for emb, photo, event in all_embeddings:
            target_vector = np.array(emb.embedding_vector)
            
            # Cosine similarity: 1 - cosine_distance
            dot_product = np.dot(query_vector, target_vector)
            norm_query = np.linalg.norm(query_vector)
            norm_target = np.linalg.norm(target_vector)
            cosine_similarity = dot_product / (norm_query * norm_target)
            
            # Convert to 0-1 range (same as pgvector calculation)
            similarity = (cosine_similarity + 1) / 2
            
            similarities.append({
                'photo_id': photo.photo_id,
                'event': event.name,
                'similarity': similarity,
                'is_same': photo.photo_id == query_photo.photo_id
            })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        print(f"\n{'Photo ID':<10} {'Event':<20} {'Similarity':<12} {'Match?'}")
        print("-" * 60)
        
        for s in similarities[:10]:  # Show top 10
            match_indicator = "✅ SAME" if s['is_same'] else ""
            print(f"{s['photo_id']:<10} {s['event']:<20} {s['similarity']:.4f}       {match_indicator}")
        
        # Check thresholds
        print("\n" + "=" * 60)
        print("THRESHOLD ANALYSIS:")
        print("=" * 60)
        
        for threshold in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
            matches = [s for s in similarities if s['similarity'] >= threshold and not s['is_same']]
            print(f"Threshold {threshold:.1f}: {len(matches)} matches (excluding same photo)")
        
        print("\n💡 Recommendation:")
        # Find best threshold that gives 1-5 matches
        for threshold in [0.5, 0.4, 0.3, 0.2]:
            matches = [s for s in similarities if s['similarity'] >= threshold and not s['is_same']]
            if 1 <= len(matches) <= 5:
                print(f"   Use threshold {threshold:.1f} for good results ({len(matches)} matches)")
                break

asyncio.run(test_search())
