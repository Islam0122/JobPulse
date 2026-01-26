# 📊 JobPulse Database Structure

Complete documentation of all database models, relationships, and data flow.

---

## 📋 Table of Contents

- [Database Overview](#database-overview)
- [Core Models](#core-models)
- [Relationships Diagram](#relationships-diagram)
- [Schema Details](#schema-details)
- [Indexes & Performance](#indexes--performance)
- [Data Flow](#data-flow)
- [Queries Reference](#queries-reference)

---

## 🗄️ Database Overview

### Stack
- **Database**: PostgreSQL 12+
- **ORM**: Django ORM
- **Cache**: Redis (for caching & sessions)
- **Backup**: Automated daily snapshots

### Databases
```
Development:  blog_db (SQLite)
Production:   jobpulse_db (PostgreSQL)
Cache:        Redis DB 0 (caching)
Bot State:    Redis DB 1 (FSM storage)
```

---

## 👥 Core Models

### 1. User (apps.users.models)

**Purpose**: Store user profiles and preferences

```python
class User(models.Model):
    # Identification
    telegram_id: BigIntegerField (unique, indexed)
    username: CharField (max_length=100, nullable)
    
    # Profile Info
    role: CharField (max_length=50, indexed)
    level: CharField (choices: junior/middle/senior/lead)
    
    # Relations
    stack: ManyToMany(Stack)              # Technologies
    work_formats: ManyToMany(WorkFormat)  # Remote/Office/Hybrid
    employment_types: ManyToMany(EmploymentType)  # Full-time/Part-time
    
    # Preferences
    location: CharField (max_length=100, nullable)
    salary_from: PositiveIntegerField (nullable)
    currency: CharField (default='USD')
    
    # Settings
    notify_mode: CharField (choices: instant/daily/weekly)
    is_active: BooleanField (default=True)
    is_profile_completed: BooleanField (default=False)
    onboarding_step: CharField (nullable)
    
    # Timestamps
    created_at: DateTimeField (auto_now_add)
    updated_at: DateTimeField (auto_now)
    
    # Indexes
    - telegram_id (PRIMARY, UNIQUE)
    - role (indexed)
    - created_at (for sorting)
```

**Size**: ~50KB per record | **Typical Count**: 1K-10K users

---

### 2. Stack (apps.users.models)

**Purpose**: Technologies/Skills catalog

```python
class Stack(models.Model):
    name: CharField (max_length=50, unique)
    
    # Indexes
    - name (UNIQUE)
    
    # Example values
    - Python, JavaScript, TypeScript
    - React, Vue.js, Angular
    - Django, FastAPI, Node.js
    - PostgreSQL, MongoDB, Redis
    - Docker, Kubernetes, AWS
```

**Size**: ~1KB per record | **Typical Count**: 50-100 techs

---

### 3. WorkFormat (apps.users.models)

**Purpose**: Work location formats

```python
class WorkFormat(models.Model):
    code: CharField (unique, max_length=20)
    title: CharField (max_length=50)
    
    # Indexes
    - code (UNIQUE)
    
    # Example values
    - remote: "Remote / Удалённо"
    - office: "Office / Офис"
    - hybrid: "Hybrid / Гибрид"
```

**Size**: <1KB per record | **Typical Count**: 3-5 formats

---

### 4. EmploymentType (apps.users.models)

**Purpose**: Job types

```python
class EmploymentType(models.Model):
    code: CharField (unique, max_length=20)
    title: CharField (max_length=50)
    
    # Example values
    - full_time: "Full-time / Полная занятость"
    - part_time: "Part-time / Частичная занятость"
    - contract: "Contract / Контракт"
    - freelance: "Freelance / Фриланс"
```

**Size**: <1KB per record | **Typical Count**: 4-6 types

---

### 5. Vacancy (apps.vacancies.models)

**Purpose**: Job vacancies (from HH.ru)

```python
class Vacancy(models.Model):
    # HH.ru Data
    hh_id: CharField (unique, indexed)
    title: CharField (max_length=255, indexed)
    description: TextField
    
    # Company Info
    company_name: CharField (max_length=255)
    company_url: URLField (nullable)
    
    # Salary
    salary_from: PositiveIntegerField (nullable)
    salary_to: PositiveIntegerField (nullable)
    currency: CharField (default='RUR')
    
    # Job Details
    location: CharField (max_length=255, nullable)
    experience: CharField (max_length=50, nullable)
    employment: CharField (max_length=50, nullable)
    schedule: CharField (max_length=50, nullable)
    
    # Content
    url: URLField
    skills: JSONField (stores list of required skills)
    
    # Status
    is_active: BooleanField (default=True, indexed)
    published_at: DateTimeField (indexed)
    
    # Relations
    notified_users: ManyToMany(User, through=VacancyNotification)
    
    # Timestamps
    created_at: DateTimeField (auto_now_add)
    updated_at: DateTimeField (auto_now)
    
    # Indexes
    - hh_id (PRIMARY, UNIQUE)
    - title (indexed)
    - is_active (indexed)
    - published_at (indexed)
    - (is_active, published_at) (composite)
```

**Size**: ~5KB per record | **Typical Count**: 10K-50K vacancies

**Skills Storage** (JSON):
```json
["Python", "Django", "PostgreSQL", "Docker", "AWS"]
```

---

### 6. VacancyNotification (apps.vacancies.models)

**Purpose**: Track notifications sent to users

```python
class VacancyNotification(models.Model):
    user: ForeignKey(User)
    vacancy: ForeignKey(Vacancy)
    
    sent_at: DateTimeField (auto_now_add)
    is_viewed: BooleanField (default=False)
    
    # Constraint
    unique_together: [('user', 'vacancy')]
    
    # Index
    - (user, vacancy) (UNIQUE)
```

**Size**: ~500B per record | **Typical Count**: 50K-500K records

---

### 7. VacancyReaction (apps.vacancies.models)

**Purpose**: User reactions to vacancies (Like/Dislike)

```python
class VacancyReaction(models.Model):
    user: ForeignKey(User)
    vacancy: ForeignKey(Vacancy)
    
    reaction: CharField (choices: like/dislike)
    created_at: DateTimeField (auto_now_add)
    
    # Constraint
    unique_together: [('user', 'vacancy')]
    
    # Index
    - (user, vacancy) (UNIQUE)
    - created_at
```

**Size**: ~500B per record | **Typical Count**: 5K-50K records

---

### 8. FavoriteVacancy (apps.vacancies.models)

**Purpose**: User favorites list

```python
class FavoriteVacancy(models.Model):
    user: ForeignKey(User)
    vacancy: ForeignKey(Vacancy)
    
    added_at: DateTimeField (auto_now_add)
    notes: TextField (nullable)  # User notes about vacancy
    
    # Constraint
    unique_together: [('user', 'vacancy')]
    
    # Index
    - (user, vacancy) (UNIQUE)
    - added_at
```

**Size**: ~1KB per record | **Typical Count**: 1K-10K records

---

### 9. ParsingLog (apps.vacancies.models)

**Purpose**: Track HH.ru parsing sessions

```python
class ParsingLog(models.Model):
    # Timing
    started_at: DateTimeField (auto_now_add)
    finished_at: DateTimeField (nullable)
    
    # Results
    total_found: IntegerField (default=0)
    new_vacancies: IntegerField (default=0)
    updated_vacancies: IntegerField (default=0)
    
    # Status
    status: CharField (choices: running/completed/failed)
    errors: TextField (nullable)
    
    # Index
    - started_at
```

**Size**: ~1KB per record | **Typical Count**: 50-100 logs/month

---

### 10. RequiredChannel (apps.channels.models)

**Purpose**: Channels user must subscribe to

```python
class RequiredChannel(models.Model):
    title: CharField (max_length=255)
    channel_id: BigIntegerField (unique)
    username: CharField (max_length=255, nullable)
    
    is_active: BooleanField (default=True)
    created_at: DateTimeField (auto_now_add)
    
    # Example
    - "Islam Dev 💎", channel_id=3063896635, username="@islam_duishobaev_dev"
```

**Size**: <1KB per record | **Typical Count**: 1-5 channels

---

### 11. BroadcastMessage (apps.broadcastprompt.models)

**Purpose**: Admin messages to all users

```python
class BroadcastMessage(models.Model):
    subject: CharField (max_length=255)
    content: TextField
    
    created_at: DateTimeField (auto_now_add)
    published_at: DateTimeField (nullable)
    is_published: BooleanField (default=False)
    
    # Index
    - created_at
```

**Size**: ~2KB per record | **Typical Count**: 10-50 messages

---

### 12. Comment (apps.review.models)

**Purpose**: User feedback

```python
class Comment(models.Model):
    user: ForeignKey(User)
    text: TextField
    
    created_at: DateTimeField (auto_now_add)
    
    # Index
    - created_at
```

**Size**: ~1KB per record | **Typical Count**: 100-1K comments

---

## 🔗 Relationships Diagram

```
┌─────────────────────────────────────────────────────────┐
│                       User                              │
├─────────────────────────────────────────────────────────┤
│ telegram_id (PK)                                        │
│ role, level, location, salary_from, currency          │
│ notify_mode, is_active, is_profile_completed          │
└─────────────────────────────────────────────────────────┘
        │                    │                    │
        │ ManyToMany         │ ManyToMany         │ ManyToMany
        ▼                    ▼                    ▼
    ┌─────┐            ┌──────────┐      ┌────────────────┐
    │Stack│            │WorkFormat│      │EmploymentType │
    └─────┘            └──────────┘      └────────────────┘

┌──────────────────────────────────────────────────────────┐
│                    Vacancy                               │
├──────────────────────────────────────────────────────────┤
│ hh_id (PK), title, description, skills (JSON)           │
│ salary_from, salary_to, location, experience           │
│ employment, schedule, published_at                     │
└──────────────────────────────────────────────────────────┘
        │                    │                    │
        │ Through            │ ForeignKey         │ ForeignKey
        │ VacancyNotif       │                    │
        ▼                    ▼                    ▼
    User          VacancyReaction          FavoriteVacancy
                                                 │
                                                 ├─ reaction (like/dislike)
                                                 ├─ added_at
                                                 └─ notes

┌────────────────────────────────────────────────┐
│           Supporting Models                    │
├────────────────────────────────────────────────┤
│ RequiredChannel  - Subscription requirements  │
│ BroadcastMessage - Admin notifications        │
│ ParsingLog      - HH.ru scraping history      │
│ Comment         - User feedback               │
└────────────────────────────────────────────────┘
```

---

## 📐 Schema Details

### User Lifecycle

```
NEW USER
   │
   ├─ Create in DB (telegram_id, role)
   │
   ├─ Onboarding (FSM stored in Redis)
   │  ├─ asking_role
   │  ├─ asking_level
   │  ├─ asking_stack
   │  ├─ asking_work_format
   │  ├─ asking_employment
   │  ├─ asking_location
   │  ├─ asking_salary
   │  └─ asking_currency
   │
   ├─ Save Profile
   │  └─ is_profile_completed = True
   │
   ├─ Active State
   │  ├─ Receives notifications
   │  ├─ Can react to vacancies
   │  └─ Can add to favorites
   │
   └─ Optional: Deactivation
      └─ is_active = False
```

### Vacancy Lifecycle

```
PARSING INITIATED
   │
   ├─ Fetch from HH.ru API
   │
   ├─ Create/Update in DB
   │  ├─ Check if hh_id exists
   │  ├─ If new: Vacancy.create()
   │  └─ If exists: Vacancy.update()
   │
   ├─ Match to Users
   │  └─ Using calculate_match_score()
   │
   ├─ Send Notifications
   │  └─ VacancyNotification.create()
   │
   ├─ Active Period
   │  ├─ Users can react (VacancyReaction)
   │  ├─ Users can favorite (FavoriteVacancy)
   │  └─ Notifications are tracked
   │
   └─ Expiration (30 days)
      └─ is_active = False
```

### Notification Flow

```
VacancyNotification.create()
   │
   ├─ Sent to User
   │
   ├─ sent_at = timezone.now()
   │
   ├─ is_viewed = False (initially)
   │
   ├─ User opens bot
   │  └─ mark_viewed() called
   │
   └─ is_viewed = True
```

---

## 🚀 Indexes & Performance

### Primary Indexes

```sql
-- User Lookups
CREATE INDEX idx_user_telegram_id ON users_user(telegram_id);
CREATE INDEX idx_user_role ON users_user(role);

-- Vacancy Searches
CREATE INDEX idx_vacancy_hh_id ON vacancies_vacancy(hh_id);
CREATE INDEX idx_vacancy_is_active ON vacancies_vacancy(is_active);
CREATE INDEX idx_vacancy_published_at ON vacancies_vacancy(published_at);

-- Composite Indexes (for matching)
CREATE INDEX idx_vacancy_active_recent 
  ON vacancies_vacancy(is_active, published_at DESC);

-- Relationship Indexes
CREATE INDEX idx_vacancy_notification_user 
  ON vacancies_vacancynotification(user_id, vacancy_id);
CREATE INDEX idx_vacancy_reaction_user 
  ON vacancies_vacancyreaction(user_id, reaction);
```

### Query Optimization Tips

```python
# ✅ GOOD: Use select_related for ForeignKey
users = User.objects.select_related('profile').all()

# ✅ GOOD: Use prefetch_related for ManyToMany
users = User.objects.prefetch_related('stack', 'work_formats')

# ✅ GOOD: Filter before joining
vacancies = Vacancy.objects.filter(
    is_active=True
).select_related('company')

# ❌ BAD: N+1 query problem
for user in users:
    print(user.stack.all())  # Query per user!

# ✅ GOOD: Batch with prefetch
users = users.prefetch_related('stack')
for user in users:
    print(user.stack.all())  # Single query
```

### Query Examples

```python
# Get user with all related data
user = User.objects.prefetch_related(
    'stack',
    'work_formats', 
    'employment_types',
    'vacancy_reactions',
    'favorite_vacancies'
).get(telegram_id=123)

# Find matching vacancies for user
from apps.vacancies.services import match_vacancy_to_users
matched_users = match_vacancy_to_users(vacancy, min_score=30)

# Get user activity stats
from django.db.models import Count
stats = {
    'likes': VacancyReaction.objects.filter(
        user=user, reaction='like'
    ).count(),
    'dislikes': VacancyReaction.objects.filter(
        user=user, reaction='dislike'
    ).count(),
    'favorites': FavoriteVacancy.objects.filter(
        user=user
    ).count(),
}
# Find active vacancies from last 24 hours
from datetime import timedelta
from django.utils import timezone

recent = Vacancy.objects.filter(
    is_active=True,
    published_at__gte=timezone.now() - timedelta(hours=24)
).order_by('-published_at')
```

---

## 📊 Data Flow

### User Profile Creation Flow

```
Telegram Message (/start)
    │
    ▼
StartHandler (bot/handlers/start.py)
    │
    ├─ Check existing profile
    │
    ├─ If new: Initialize FSM states
    │   └─ State stored in Redis DB 1
    │
    ├─ Collect data:
    │  ├─ Role (waiting_for_role)
    │  ├─ Level (waiting_for_level)
    │  ├─ Stack (waiting_for_stack)
    │  ├─ WorkFormats (waiting_for_work_format)
    │  ├─ EmploymentTypes (waiting_for_employment)
    │  ├─ Location (waiting_for_location)
    │  ├─ Salary (waiting_for_salary)
    │  └─ Currency (waiting_for_currency)
    │
    ▼
APIClient.create_user() (bot/services/api_client.py)
    │
    ▼
UserViewSet.create() (backend/apps/users/views.py)
    │
    ├─ Validate data
    │
    ├─ Create User instance
    │  └─ INSERT INTO users_user (telegram_id, role, level, ...)
    │
    ├─ Add Stack relations
    │  └─ INSERT INTO users_user_stack
    │
    ├─ Add WorkFormats
    │  └─ INSERT INTO users_user_work_formats
    │
    ├─ Add EmploymentTypes
    │  └─ INSERT INTO users_user_employment_types
    │
    └─ Cache invalidation
       └─ Delete from Redis: user:{telegram_id}
```

### Vacancy Parsing Flow

```
Celery Beat (every 30 min)
    │
    ├─ @beat_schedule['parse-hh-vacancies']
    │
    ▼
parse_hh_vacancies() (backend/apps/vacancies/tasks.py)
    │
    ├─ ParsingLog.create(status='running')
    │
    ├─ For each search query:
    │  │
    │  ├─ fetch_vacancies_from_hh(query)
    │  │  └─ HH.ru API → Rate-limited requests
    │  │
    │  └─ save_vacancies_batch()
    │     ├─ Check if hh_id exists
    │     ├─ Create new: INSERT INTO vacancies_vacancy
    │     └─ Update existing: UPDATE vacancies_vacancy
    │
    ├─ Update ParsingLog
    │  └─ status='completed', new_vacancies=X, updated=Y
    │
    └─ Trigger notify_users_about_new_vacancies
```

### Notification Sending Flow

```
notify_users_about_new_vacancies() Task
    │
    ├─ Find recent vacancies (created < 1 hour)
    │
    ├─ For each vacancy:
    │  │
    │  ├─ match_vacancy_to_users_v2(vacancy)
    │  │  ├─ Calculate match score (0-100)
    │  │  │  ├─ Role match (35%)
    │  │  │  ├─ Level match (20%)
    │  │  │  ├─ Stack match (25%)
    │  │  │  ├─ Salary match (10%)
    │  │  │  └─ Location match (10%)
    │  │  │
    │  │  └─ Return users with score > 30
    │  │
    │  ├─ Filter already notified
    │  │
    │  └─ For each matched user:
    │     │
    │     ├─ send_vacancy_notification(user, vacancy)
    │     │  └─ Telegram Bot API call
    │     │
    │     ├─ Check response status
    │     │  ├─ 200: Success
    │     │  ├─ 403: Bot blocked by user
    │     │  └─ 400: Chat not found
    │     │
    │     └─ VacancyNotification.create()
    │        └─ INSERT INTO vacancies_vacancynotification
    │
    └─ Update notification count
```

---

## 📚 Queries Reference

### Common Queries

```python
# 1. Get all active users with full profile
active_users = User.objects.filter(
    is_active=True,
    is_profile_completed=True
).prefetch_related(
    'stack',
    'work_formats',
    'employment_types'
)

# 2. Get user statistics
from django.db.models import Count, Q

user_stats = User.objects.annotate(
    reactions_count=Count('vacancy_reactions'),
    favorites_count=Count('favorite_vacancies'),
    likes_count=Count(
        'vacancy_reactions',
        filter=Q(vacancy_reactions__reaction='like')
    ),
    notifications_count=Count('notified_vacancies')
)

# 3. Get trending technologies
from django.db.models import Count

trending_stacks = Stack.objects.annotate(
    user_count=Count('users')
).order_by('-user_count')[:10]

# 4. Get engagement metrics
from django.db.models import Avg

engagement = {
    'avg_reactions_per_user': (
        VacancyReaction.objects.values('user')
        .annotate(Count('id'))
        .aggregate(Avg('id__count'))['id__count__avg']
    ),
    'avg_favorites_per_user': (
        FavoriteVacancy.objects.values('user')
        .annotate(Count('id'))
        .aggregate(Avg('id__count'))['id__count__avg']
    ),
}

# 5. Get vacancy statistics
vacancy_stats = {
    'total_active': Vacancy.objects.filter(is_active=True).count(),
    'notified_last_24h': VacancyNotification.objects.filter(
        sent_at__gte=timezone.now() - timedelta(hours=24)
    ).count(),
    'avg_salary': Vacancy.objects.filter(
        salary_from__isnull=False
    ).aggregate(Avg('salary_from'))['salary_from__avg'],
}

# 6. Get users by level
users_by_level = User.objects.values('level').annotate(
    count=Count('id')
).order_by('level')

# 7. Get top companies
from django.db.models import Count

top_companies = Vacancy.objects.values('company_name').annotate(
    vacancy_count=Count('id')
).order_by('-vacancy_count')[:20]
```

### Redis Caching Strategy

```python
# Cache user profile
from django.core.cache import cache

cache_key = f'user:{telegram_id}'
user_data = cache.get(cache_key)

if not user_data:
    user = User.objects.get(telegram_id=telegram_id)
    serializer = UserReadSerializer(user)
    cache.set(cache_key, serializer.data, 300)  # 5 minutes

# Cache vacancy recommendations
cache_key = f'user_recommendations:{telegram_id}'
recommendations = cache.get(cache_key)

if not recommendations:
    # Calculate recommendations
    recommendations = get_personalized_vacancies(user)
    cache.set(cache_key, recommendations, 600)  # 10 minutes

# Invalidate cache
cache.delete(f'user:{telegram_id}')
cache.delete_pattern('user_recommendations:*')
```

---

## 🔄 Data Consistency

### Transaction Management

```python
# Critical operations use transactions
from django.db import transaction

@transaction.atomic
def create_user_with_relations(user_data):
    """Ensure all or nothing"""
    user = User.objects.create(**user_data)
    
    # If any of these fail, entire transaction rolls back
    user.stack.set(user_data['stack_ids'])
    user.work_formats.set(user_data['work_format_ids'])
    user.employment_types.set(user_data['employment_type_ids'])
    
    return user

# Bulk operations
with transaction.atomic():
    VacancyNotification.objects.bulk_create(
        notifications,
        batch_size=100
    )
```

### Unique Constraints

```python
# Prevent duplicate user registrations
class Meta:
    unique_together = [('user', 'vacancy')]  # VacancyNotification
    unique_together = [('user', 'vacancy')]  # VacancyReaction
    unique_together = [('user', 'vacancy')]  # FavoriteVacancy
```

---

**Last Updated**: January 2026 | **Database Version**: PostgreSQL 12+