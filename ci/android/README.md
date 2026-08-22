# CI-only Android module

This is not a real app. It exists purely so CI can compile `Hardbrut.kt`
(the file at the repo root) against a real Jetpack Compose classpath, since
that file has no build system of its own — it's meant to be dropped
directly into a consumer's project.

`app/build.gradle.kts` points the Kotlin source set at the repo root
directly (`rootProject.projectDir.parentFile.parentFile`) rather than
copying `Hardbrut.kt` in here, so there's nothing to keep in sync.

Run locally with:

```sh
cd ci/android
gradle :app:compileDebugKotlin
```
