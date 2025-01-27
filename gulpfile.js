const gulp = require('gulp');
const sass = require('gulp-sass')(require('sass'));
const cleanCSS = require('gulp-clean-css');
const uglify = require('gulp-uglify');
const rename = require('gulp-rename');
const path = require('path');
const fs = require('fs');

function getOutputPath(fileType) {
    return path.resolve('static/dist', fileType);
}

// Compile SCSS to CSS and minify it
gulp.task('sass', function() {
    return gulp.src('static/src/css/*.scss')
        .pipe(sass().on('error', sass.logError))
        .pipe(cleanCSS({
            compatibility: 'ie8',
            level: 2
        }))
        .pipe(rename({ suffix: '.min' }))
        .pipe(gulp.dest(getOutputPath('css')));
});

// Handle CSS files - copy .min.css directly, process others
gulp.task('minify-css', function() {
    gulp.src('static/src/css/*.min.css')
        .pipe(gulp.dest(getOutputPath('css')));
    
    return gulp.src(['static/src/css/*.css', '!static/src/css/*.min.css'])
        .pipe(cleanCSS({
            compatibility: 'ie8',
            level: 2
        }))
        .pipe(rename({ suffix: '.min' }))
        .pipe(gulp.dest(getOutputPath('css')));
});

// Handle JS files - copy .min.js directly, process others
gulp.task('js', function() {
    gulp.src('static/src/js/*.min.js')
        .pipe(gulp.dest(getOutputPath('js')));
    
    return gulp.src(['static/src/js/*.js', '!static/src/js/*.min.js'])
        .pipe(uglify({
            compress: true,
            mangle: true,
            output: {
                comments: false
            }
        }))
        .pipe(rename({ suffix: '.min' }))
        .pipe(gulp.dest(getOutputPath('js')));
});

// Copy plugins folder
gulp.task('plugins', function() {
    return gulp.src('static/src/plugins/**/*')
        .pipe(gulp.dest(getOutputPath('plugins')));
});

// Copy assets folder
gulp.task('assets', function(done) {
    const srcDir = 'static/src/assets';
    const destDir = 'static/dist/assets';

    fs.cpSync(srcDir, destDir, { recursive: true });
    done();
});

// Delete files from dist if they no longer exist in src
function cleanDeletedFiles(done) {
    const srcDirs = ['static/src/css', 'static/src/js', 'static/src/assets', 'static/src/plugins'];
    const distDirs = ['static/dist/css', 'static/dist/js', 'static/dist/assets', 'static/dist/plugins'];

    distDirs.forEach((distDir, index) => {
        const srcDir = srcDirs[index];
        fs.readdirSync(distDir).forEach(file => {
            const srcFilePath = path.join(srcDir, file);
            const distFilePath = path.join(distDir, file);
            if (!fs.existsSync(srcFilePath)) {
                fs.rmSync(distFilePath, { recursive: true, force: true });
            }
        });
    });
    done();
}

// Watch files for changes
gulp.task('watch', function() {
    gulp.watch('static/src/css/*.scss', gulp.series('sass'));
    gulp.watch('static/src/css/*.css', gulp.series('minify-css'));
    gulp.watch('static/src/js/*.js', gulp.series('js'));
    gulp.watch('static/src/plugins/**/*', gulp.series('plugins'));
    gulp.watch('static/src/assets/**/*', gulp.series('assets'));
    gulp.watch(['static/src/**/*'], gulp.series(cleanDeletedFiles));
});

// Default task
gulp.task('default', gulp.series('sass', 'minify-css', 'js', 'plugins', 'assets', 'watch'));
