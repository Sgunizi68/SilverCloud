# Gemine – Development Principles & Standards

## General Principles
- Build the application as a **server-rendered monolith**
- Prefer simplicity and clarity over architectural complexity
- Write clean, readable, and maintainable code
- Follow DRY (Don't Repeat Yourself) principles
- Use meaningful variable, function, and template names
- Keep functions small and focused on a single responsibility
- Write self-documenting code with clear intent
- Prioritize code readability over cleverness
- Use consistent formatting and indentation
- Handle errors gracefully and provide meaningful error messages

---

## Architecture Principles (Server-Rendered Monolith)
- The application MUST follow a **2-layer architecture**:
  - **Application Layer**: server-side web application (UI + business logic + data access)
  - **Database Layer**
- Do NOT introduce a separate API/service layer unless explicitly required
- UI rendering, business logic, and database access live in the **same deployable application**
- The application communicates **directly with the database**
- Avoid microservices, distributed systems, or unnecessary abstractions
- Prefer synchronous request/response flows
- The system must be deployable as a **single artifact**

---

## Code Structure & Organization
- Organize code into logical modules and directories
- Group code by **feature/domain**, not by technical layer
- Keep routing, business logic, and data access **close but organized**
- Use clear boundaries inside the application (modules/packages)
- Use consistent file naming conventions:
  - kebab-case for files
  - PascalCase for classes
- Keep configuration strictly separate from code
- Avoid over-engineered patterns (excessive interfaces, factories, adapters)
- Use dependency injection where it adds clarity (not ceremony)

---

## UI & Rendering Rules
- UI MUST be **server-rendered**
- Templates are part of the backend application
- Avoid heavy frontend frameworks unless strictly necessary
- Use JavaScript only for progressive enhancement
- Business rules must NEVER live in templates
- Templates should focus on presentation, not logic
- Reuse layouts, partials, and components consistently

---

## Data Access Rules
- The application layer accesses the database directly
- Use ORM or query builders consistently
- Centralize database access logic
- Avoid spreading raw SQL across the codebase
- Use transactions for multi-step operations
- Minimize database round-trips
- Avoid business logic inside the database (no logic-heavy stored procedures)

---

## Documentation & Comments
- Write clear, concise comments that explain **WHY**, not **WHAT**
- Use docstrings for public functions and classes
- Keep README files up to date
- Document architectural decisions and trade-offs
- Avoid obvious comments that restate the code
- Use TODO comments sparingly and track them properly

---

## Testing Best Practices
- Write unit tests for business logic
- Prefer testing application logic without rendering when possible
- Use descriptive test names that explain the scenario
- Follow AAA pattern: Arrange, Act, Assert
- Mock external dependencies
- Write integration tests for critical user workflows
- Tests should reflect real user behavior in server-rendered flows

---

## Performance Considerations
- Optimize for readability first, performance second
- Profile before optimizing
- Avoid premature optimization
- Cache expensive computations where appropriate
- Use pagination and lazy loading for large datasets
- Minimize database queries in request lifecycle

---

## Security Guidelines
- Validate all inputs server-side
- Sanitize outputs rendered into templates
- Use parameterized queries to prevent SQL injection
- Implement authentication and role-based authorization centrally
- Store secrets in environment variables, never in code
- Use HTTPS for all communications
- Follow principle of least privilege
- Keep dependencies updated and audited

---

## Language-Specific Rules

### Python
- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Use context managers (`with`) for resource management
- Handle exceptions explicitly; avoid bare `except`
- Use virtual environments for dependency management
- Write docstrings for all public functions and classes

### Java (Spring Boot)
- Prefer constructor-based dependency injection
- Keep controllers thin and readable
- Avoid unnecessary DTO layers unless justified
- Use clear package naming by feature/domain
- Prefer composition over inheritance

---

## Backend & Routing
- Routes/controllers are responsible for:
  - Request handling
  - Validation
  - Calling business logic
  - Returning rendered views
- Do NOT design the app as an API-first system
- Use proper HTTP status codes even for server-rendered flows
- Centralize cross-cutting concerns (auth, logging, error handling)

---

## Git & Version Control
- Write clear, descriptive commit messages
- Keep commits small and focused
- Use feature branches
- Squash commits before merging to main
- Never commit secrets, credentials, or environment files
- Tag releases appropriately

---

## Code Review Guidelines
- Review for correctness, clarity, and simplicity
- Watch for unnecessary abstractions
- Ensure server-rendered approach is respected
- Verify tests and documentation
- Suggest improvements constructively
- Approve only when confident in long-term maintainability

---

## Environment & Configuration
- Use environment variables for all configuration
- Separate configs for dev, test, and production
- Use `.env` files only for local development
- Validate configuration at application startup
- Document all required environment variables

---

## Error Handling & Logging
- Use centralized error handling
- Log errors with sufficient context
- Avoid leaking sensitive data to UI
- Provide user-friendly error pages
- Monitor error rates and logs

---

## Dependencies & Libraries
- Keep dependencies minimal and justified
- Prefer mature, well-maintained libraries
- Regularly update and audit dependencies
- Remove unused libraries promptly
- Document rationale for major dependencies

---

## Monitoring & Observability
- Implement structured logging
- Log important business events
- Add health check endpoints
- Monitor performance and resource usage
- Set alerts for critical failures

---

## Code Quality Tools
- Use linters and formatters
- Enforce consistent code style
- Use CI/CD for automated checks
- Fail builds on linting or test errors
- Keep CI simple and fast
