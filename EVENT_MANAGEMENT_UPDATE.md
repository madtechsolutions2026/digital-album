# ✅ Event Management Added

## What's New

Admins can now **create and manage multiple wedding events** directly from the admin interface!

## Features Added

### 1. **Event Management API** (`/api/events`)
- `POST /api/events` - Create new event
- `GET /api/events` - List all events with photo counts
- `GET /api/events/{id}` - Get event details
- `DELETE /api/events/{id}` - Delete event (and all photos)

### 2. **Admin UI Updates**
- **Event Grid**: Visual display of all events
- **Create Event Button**: Quick event creation
- **Event Selection**: Click to select event for upload
- **Photo Counts**: See how many photos in each event
- **Auto-Selection**: First event auto-selected

## How to Use

### Create New Event
1. Go to `/admin`
2. Click **"+ New Event"** button
3. Enter event name (e.g., "John & Jane Wedding")
4. Optionally add event date
5. Click **"Create Event"**
6. Event is created and auto-selected!

### Upload Photos to Event
1. Select an event from the grid (or create new one)
2. Choose files or folder
3. Click **"Upload"**
4. Photos uploaded to selected event!

### View Event Photos
1. Go to `/gallery`
2. Select event from dropdown (coming soon!)
3. View all photos from that event

## What Changed

### Backend
- **Created**: `app/api/routes/events.py` - Event CRUD operations
- **Updated**: `app/main.py` - Registered events router
- **Updated**: `app/api/routes/__init__.py` - Exported events router

### Frontend
- **Updated**: `AdminPage.jsx` - Added event management UI
- **Updated**: `AdminPage.css` - Styled event cards and forms

### Database
- No changes needed! Events table already exists
- Foreign key cascades handle photo deletion

## Event Card Features

Each event card shows:
- 📅 Event name
- 📅 Event date (if provided)
- 📸 Photo count
- Selected state (highlighted)

## Benefits

✅ **Multi-Client Support** - One event per wedding
✅ **Organization** - Keep photos separate
✅ **Easy Switching** - Click to change events
✅ **Photo Counts** - See progress at a glance
✅ **No Manual IDs** - No more "Event 2 not found" errors!

## Example Workflow

```
1. Admin logs in → /admin
2. Clicks "+ New Event"
3. Enters "Smith Wedding - June 2026"
4. Adds date: 2026-06-15
5. Clicks "Create Event"
6. Event appears in grid (auto-selected)
7. Uploads 50 wedding photos
8. Card updates: "📸 50 photos"
9. Creates another event for next wedding
10. Repeat!
```

## API Examples

### Create Event
```bash
POST /api/events
{
  "name": "Smith Wedding",
  "event_date": "2026-06-15"
}

Response:
{
  "success": true,
  "message": "Event created successfully",
  "data": {
    "event_id": 2,
    "name": "Smith Wedding",
    "event_date": "2026-06-15",
    "created_at": "2026-07-21T10:30:00"
  }
}
```

### List Events
```bash
GET /api/events

Response:
{
  "success": true,
  "message": "Retrieved 3 events",
  "data": {
    "events": [
      {
        "event_id": 3,
        "name": "Johnson Wedding",
        "event_date": "2026-08-01",
        "created_at": "2026-07-21T10:00:00",
        "photo_count": 120
      },
      {
        "event_id": 2,
        "name": "Smith Wedding",
        "event_date": "2026-06-15",
        "created_at": "2026-07-20T14:30:00",
        "photo_count": 50
      },
      {
        "event_id": 1,
        "name": "Test Event",
        "event_date": null,
        "created_at": "2026-07-15T09:00:00",
        "photo_count": 5
      }
    ],
    "total": 3
  }
}
```

### Delete Event
```bash
DELETE /api/events/2

Response:
{
  "success": true,
  "message": "Event 'Smith Wedding' deleted successfully",
  "data": {
    "event_id": 2
  }
}
```

## Future Enhancements

### Gallery Event Selector
- Add dropdown in gallery to view specific event
- Currently gallery shows all photos from all events
- Easy to add: filter by event_id

### Event Analytics
- Most photos uploaded
- Average faces per photo
- Upload date range
- Storage used per event

### Event Settings
- Event description
- Client contact info
- Event status (active/archived)
- Private access codes

### Bulk Operations
- Move photos between events
- Merge events
- Archive old events
- Export event data

## Testing

1. **Create Event**:
   ```bash
   curl -X POST http://localhost:8000/api/events \
     -H "Content-Type: application/json" \
     -d '{"name":"Test Wedding","event_date":"2026-12-31"}'
   ```

2. **List Events**:
   ```bash
   curl http://localhost:8000/api/events
   ```

3. **Upload to Event**:
   ```bash
   # Use admin UI to upload photos
   # Or use API directly
   ```

## Migration Note

**Existing Photos**: All existing photos are already associated with Event 1. No migration needed!

If you want to organize them:
1. Create proper events
2. Use SQL to reassign photos:
   ```sql
   UPDATE photos SET event_id = 2 
   WHERE photo_id IN (SELECT photo_id FROM photos LIMIT 10);
   ```

## Security Note

⚠️ **No Authentication Yet**: Anyone can create/delete events. 

**For Production**:
- Add photographer authentication
- Require login to access /admin
- Add role-based permissions
- Protect event deletion (require confirmation)

## Summary

✅ Event management UI complete  
✅ Create events with names and dates  
✅ Visual event selection  
✅ Photo counts displayed  
✅ No more "Event not found" errors  
✅ Ready to manage multiple weddings!

**Try it now**: Go to `/admin` and create your first real event! 🎉
