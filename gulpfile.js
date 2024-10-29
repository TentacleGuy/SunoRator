const gulp = require('gulp');
const sass = require('gulp-sass')(require('sass'));
const cleanCSS = require('gulp-clean-css');
const uglify = require('gulp-uglify');
const rename = require('gulp-rename');
const path = require('path');

// Function to get the output path for a given source path
function getOutputPath(fileType) {
    return path.resolve('static/dist', fileType);
}

// Compile SCSS to CSS and minify it
gulp.task('sass', function() {
    return gulp.src('static/src/css/*.scss')
        .pipe(sass().on('error', sass.logError))  // Compile SCSS to CSS
        .pipe(cleanCSS())  // Minify CSS
        .pipe(rename({ suffix: '.min' }))  // Add .min suffix
        .pipe(gulp.dest(getOutputPath('css')));  // Save to 'dist/css'
});

// Minify existing CSS files and rename with .min suffix
gulp.task('minify-css', function() {
    return gulp.src('static/src/css/*.css')
        .pipe(cleanCSS())  // Minify CSS
        .pipe(rename({ suffix: '.min' }))  // Add .min suffix
        .pipe(gulp.dest(getOutputPath('css')));  // Save to 'dist/css'
});

// Minify JavaScript files and rename with .min suffix
gulp.task('js', function() {
    return gulp.src('static/src/js/*.js')
        .pipe(uglify())  // Minify JavaScript
        .pipe(rename({ suffix: '.min' }))  // Add .min suffix
        .pipe(gulp.dest(getOutputPath('js')));  // Save to 'dist/js'
});

// Watch files for changes
gulp.task('watch', function() {
    gulp.watch('static/src/css/*.scss', gulp.series('sass'));
    gulp.watch('static/src/css/*.css', gulp.series('minify-css'));
    gulp.watch('static/src/js/*.js', gulp.series('js'));
});

// Default task
gulp.task('default', gulp.series('sass', 'minify-css', 'js', 'watch'));
