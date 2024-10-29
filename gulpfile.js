const gulp = require('gulp');
const sass = require('gulp-sass')(require('sass'));
const cleanCSS = require('gulp-clean-css');
const uglify = require('gulp-uglify');
const rename = require('gulp-rename');
const path = require('path');

function getOutputPath(fileType) {
    return path.resolve('static/dist', fileType);
}

// Compile SCSS to CSS and minify it
gulp.task('sass', function() {
    return gulp.src('static/src/css/*.scss')
        .pipe(sass().on('error', sass.logError))
        .pipe(cleanCSS())
        .pipe(rename({ suffix: '.min' }))
        .pipe(gulp.dest(getOutputPath('css')));
});

// Handle CSS files - copy .min.css directly, process others
gulp.task('minify-css', function() {
    // Copy pre-minified CSS files directly
    gulp.src('static/src/css/*.min.css')
        .pipe(gulp.dest(getOutputPath('css')));
    
    // Process non-minified CSS files
    return gulp.src(['static/src/css/*.css', '!static/src/css/*.min.css'])
        .pipe(cleanCSS())
        .pipe(rename({ suffix: '.min' }))
        .pipe(gulp.dest(getOutputPath('css')));
});

// Handle JS files - copy .min.js directly, process others
gulp.task('js', function() {
    // Copy pre-minified JS files directly
    gulp.src('static/src/js/*.min.js')
        .pipe(gulp.dest(getOutputPath('js')));
    
    // Process non-minified JS files
    return gulp.src(['static/src/js/*.js', '!static/src/js/*.min.js'])
        .pipe(uglify())
        .pipe(rename({ suffix: '.min' }))
        .pipe(gulp.dest(getOutputPath('js')));
});

// Watch files for changes
gulp.task('watch', function() {
    gulp.watch('static/src/css/*.scss', gulp.series('sass'));
    gulp.watch('static/src/css/*.css', gulp.series('minify-css'));
    gulp.watch('static/src/js/*.js', gulp.series('js'));
});

// Default task
gulp.task('default', gulp.series('sass', 'minify-css', 'js', 'watch'));
