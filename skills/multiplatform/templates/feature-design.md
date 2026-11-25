# Feature design: <Feature>
<!-- About 24 KB at most, so a dependent feature can read it in one Read. Signatures and types, not implementations; cite architecture sections instead of restating them. Other features read only §2 Domain. -->

| FR IDs | Platforms | Owner | Status | UI designs |
|---|---|---|---|---|
| FR-001, FR-002 | Both | <developer> | Draft | <Figma link, including iOS adaptations> |

## 1. Screens
| Screen | Route (arguments) | States | Back affordance | Notes |
|---|---|---|---|---|
| Notes list | `NotesRoute` | Loading, Empty, Success, Error | Root: none | Snackbar when a refresh fails over cached notes |

### <Screen>: state, actions and events
```kotlin
sealed interface NotesUiState { /* Loading, Empty, Success(notes), Error(message: StringResource) */ }
sealed interface NotesAction { /* user intents sent to the ViewModel */ }
sealed interface NotesEvent { /* transient UI only, e.g. ShowMessage(message: StringResource) */ }
```
- Survives Android process death: <fields kept in SavedStateHandle>
- Survives iOS termination: <data written to local storage, e.g. drafts>

## 2. Domain
```kotlin
data class Note(val id: String, val title: String, val body: String, val updatedAt: Instant)

interface NoteRepository {
    fun observeNotes(): Flow<List<Note>>
    suspend fun refresh(): AppResult<Unit>
}

class ObserveNotesUseCase(noteRepository: NoteRepository) { operator fun invoke(): Flow<List<Note>> }
class RefreshNotesUseCase(noteRepository: NoteRepository) { suspend operator fun invoke(): AppResult<Unit> }
```

## 3. Data
| Endpoint | Request | Response | Errors |
|---|---|---|---|
| `GET /v1/notes` | — | `List<NoteDto>` | 401, 5xx |

- **Room:**
  - entity `NoteEntity` (`id` as the primary key; index on `updatedAt`);
  - DAO `observeAll(): Flow<List<NoteEntity>>`, `suspend fun upsertAll(…)`;
  - migration <n> → <n+1>: <SQL, or "none">.
- **DataStore keys:** <…>
- **SecureStore keys:** <…>
- **Cache and refresh:** <following the architecture's data strategy>

## 4. Platform notes
"None" is a valid answer: the feature is fully shared.

| Part | Common API | Android (`androidMain`) | iOS (`iosMain` / Swift) | Permission / usage description |
|---|---|---|---|---|
| e.g. Share a note | `ShareService.share(text)` | Share sheet intent | `UIActivityViewController` | — |

- iOS adaptations from the look-and-feel ADR: <…>
- Platform matrix change needed: <no / CR-…>

## 5. Diagrams
<!-- Only when STATUS.md has Design diagrams = On; otherwise write "Off (STATUS.md: Design diagrams)." and keep the heading. The diagrams picture §1–§4 and add no facts: a new class or call goes into §1–§4 first. Names, stereotypes and key public members only; full signatures stay above. Mark each platform implementation <<androidMain>>, <<iosMain>> or <<iosApp Swift>>. About 4 KB for the whole section. Phase 4 KDocs link here. -->

### Class diagram
```mermaid
classDiagram
  namespace presentation {
    class NotesScreen
    class NotesViewModel {
      +uiState
      +onAction(NotesAction)
    }
    class NotesUiState {
      <<sealed>>
    }
  }
  namespace domain {
    class ObserveNotesUseCase
    class RefreshNotesUseCase
    class NoteRepository {
      <<interface>>
      +observeNotes()
      +refresh()
    }
  }
  namespace data {
    class NoteRepositoryImpl
    class NoteApi
    class NoteDao {
      <<interface>>
    }
  }
  namespace platform {
    class ShareService {
      <<interface>>
      +share(text)
    }
    class AndroidShareService {
      <<androidMain>>
    }
    class IosShareService {
      <<iosMain>>
    }
  }
  NotesScreen --> NotesViewModel
  NotesViewModel --> NotesUiState
  NotesViewModel --> ObserveNotesUseCase
  NotesViewModel --> RefreshNotesUseCase
  NotesViewModel --> ShareService
  ObserveNotesUseCase --> NoteRepository
  RefreshNotesUseCase --> NoteRepository
  NoteRepositoryImpl ..|> NoteRepository
  NoteRepositoryImpl --> NoteApi
  NoteRepositoryImpl --> NoteDao
  AndroidShareService ..|> ShareService
  IosShareService ..|> ShareService
```

### Sequence: <flow, e.g. open and refresh the notes list>
<!-- One per primary flow, at most 3 (e.g. load, refresh, save). The failure path goes in an alt block and ends in the behaviour from §6 Errors. A flow that crosses into platform code shows the common interface as the participant, with the platform in a note. -->
```mermaid
sequenceDiagram
  actor User
  participant Screen as NotesScreen
  participant VM as NotesViewModel
  participant Observe as ObserveNotesUseCase
  participant Refresh as RefreshNotesUseCase
  participant Repo as NoteRepository
  participant Dao as NoteDao
  participant Api as NoteApi
  User->>Screen: open
  Screen->>VM: collect uiState
  VM->>Observe: invoke()
  Observe->>Repo: observeNotes()
  Repo->>Dao: observeAll()
  Dao-->>VM: Flow emits cached notes
  VM-->>Screen: Success(notes) or Empty
  VM->>Refresh: invoke()
  Refresh->>Repo: refresh()
  Repo->>Api: GET /v1/notes
  alt 200
    Api-->>Repo: List<NoteDto>
    Repo->>Dao: upsertAll(entities)
    Dao-->>VM: Flow emits new notes
  else Network error
    Api-->>Repo: IOException
    Repo-->>VM: AppResult.Failure(Network)
    VM-->>Screen: snackbar (§6: error_network)
  end
```

## 6. Errors
| AppError | Message (string resource) | UI behaviour |
|---|---|---|
| Network | `error_network` | Error state with Retry; or a snackbar if cached notes are shown |
| Unauthorized | `error_session_expired` | Go to sign-in |

## 7. Analytics
| Event | Parameters | Trigger |
|---|---|---|

## 8. Accessibility and i18n
- Content descriptions
- Headings
- Focus order
- New strings and plurals (`composeResources/values/strings.xml`)
- Locale-aware formatting
- RTL notes

## 9. Test cases
| ID | Level | FR | Platforms | Case |
|---|---|---|---|---|
| IT-001 | Integration | FR-001 | Both (`commonTest`) | Refresh stores the notes; the DAO emits them |
| UI-001 | UI | FR-001 | Both | Empty state shows "Create note", which opens the editor |
| IT-002 | Integration | FR-002 | iOS (`iosTest`) | `ShareService` presents the share sheet |

## 10. PR slice plan
| # | PR | Layer | Est. changed lines |
|---|---|---|---|
| 1 | Note model, repository interface, UseCases + tests | Domain | ~200 |
| 2 | Ktor API, Room, repository implementation + tests | Data | ~350 |
| 3 | Platform implementations + platform tests | Platform | ~200 |
| 4 | UiState, ViewModel + tests | Presentation | ~250 |
| 5 | Screen and content, previews, navigation, Koin | Presentation | ~300 |
| 6 | Critical-flow UI test (both platforms) | Test | ~100 |

## 11. Open questions
- <…>
