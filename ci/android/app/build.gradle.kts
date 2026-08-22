plugins {
    id("com.android.library")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

android {
    namespace = "com.example.hardbrut"
    compileSdk = 34

    defaultConfig {
        minSdk = 24
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
    }
}

kotlin {
    // Hardbrut.kt lives at the repo root, not in this module — point the
    // source set at it directly instead of copying it (see ci/android/README.md).
    sourceSets["main"].kotlin.srcDir(rootProject.projectDir.parentFile.parentFile)
}

dependencies {
    val composeBom = platform("androidx.compose:compose-bom:2024.09.02")
    implementation(composeBom)
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.foundation:foundation")
    implementation("androidx.compose.material3:material3")
    // rememberRipple() — for the custom black-15%-alpha press indication
    implementation("androidx.compose.material:material-ripple")
}
