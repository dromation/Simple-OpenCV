// SimpleOpenCV portable launcher. MIT; see the bundled LICENSE and notices.
package main

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"embed"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io/fs"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"os/signal"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"
)

//go:embed all:site
var assets embed.FS
var version = "0.6.0"

func verify(site fs.FS) error {
	data, err := fs.ReadFile(site, "PACKAGE-MANIFEST.json")
	if err != nil {
		return err
	}
	var manifest map[string]string
	if err = json.Unmarshal(data, &manifest); err != nil {
		return err
	}
	for _, required := range []string{"index.html", "browser-worker.js", "vendor/opencv24/opencv24.js", "vendor/opencv.js", "LICENSE", "about.html"} {
		if manifest[required] == "" {
			return fmt.Errorf("missing required asset: %s", required)
		}
	}
	for name, want := range manifest {
		data, err := fs.ReadFile(site, name)
		if err != nil {
			return err
		}
		sum := sha256.Sum256(data)
		if hex.EncodeToString(sum[:]) != want {
			return fmt.Errorf("asset checksum mismatch: %s", name)
		}
	}
	return nil
}

func handler(site fs.FS, host, token string, quit func()) http.Handler {
	files := http.FileServer(http.FS(site))
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Bound to loopback; exact Host validation also prevents DNS rebinding.
		if r.Host != host {
			http.Error(w, "Local requests only", http.StatusForbidden)
			return
		}
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Cache-Control", "no-cache")
		if r.URL.Path == "/portable-host.js" {
			if r.Method != "GET" {
				http.Error(w, "Method not allowed", 405)
				return
			}
			w.Header().Set("Content-Type", "text/javascript; charset=utf-8")
			data, _ := json.Marshal(map[string]any{"portable": true, "version": version, "platform": runtime.GOOS + "/" + runtime.GOARCH, "shutdownToken": token})
			fmt.Fprintf(w, "window.SimpleOpenCVHost=%s;", data)
			return
		}
		if r.URL.Path == "/__simpleopencv/quit" {
			if r.Method != "POST" {
				http.Error(w, "Method not allowed", 405)
				return
			}
			if r.Header.Get("Origin") != "http://"+host || r.Header.Get("X-SimpleOpenCV-Token") != token {
				http.Error(w, "Forbidden", 403)
				return
			}
			w.WriteHeader(http.StatusNoContent)
			go quit()
			return
		}
		if r.Method != "GET" && r.Method != "HEAD" {
			http.Error(w, "Method not allowed", 405)
			return
		}
		// No directory listings; no access to arbitrary local files.
		name := strings.TrimPrefix(r.URL.Path, "/")
		if name == "" {
			name = "index.html"
		}
		info, err := fs.Stat(site, name)
		if err != nil || info.IsDir() {
			http.NotFound(w, r)
			return
		}
		files.ServeHTTP(w, r)
	})
}

func openBrowser(url string) error {
	var command *exec.Cmd
	switch runtime.GOOS {
	case "windows":
		command = exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	case "darwin":
		command = exec.Command("open", url)
	default:
		command = exec.Command("xdg-open", url)
	}
	if err := command.Start(); err != nil {
		return err
	}
	go command.Wait()
	return nil
}

func main() {
	port := flag.Int("port", 8767, "Local port (keep the same port to retain browser projects)")
	noBrowser := flag.Bool("no-browser", false, "Print the URL without opening the browser")
	check := flag.Bool("check", false, "Verify embedded application files and exit")
	showVersion := flag.Bool("version", false, "Print version and exit")
	flag.Parse()
	if *showVersion {
		fmt.Printf("SimpleOpenCV %s · %s/%s · OpenCV 2.4.13.7 + 4.13.0\n", version, runtime.GOOS, runtime.GOARCH)
		return
	}
	site, err := fs.Sub(assets, "site")
	if err != nil {
		log.Fatal(err)
	}
	if err = verify(site); err != nil {
		log.Fatal("Embedded application: ", err)
	}
	if *check {
		fmt.Println("SimpleOpenCV: embedded application and both OpenCV engines verified")
		return
	}
	if *port < 1 || *port > 65535 {
		log.Fatal("Choose a port between 1 and 65535")
	}
	host := net.JoinHostPort("127.0.0.1", strconv.Itoa(*port))
	url := "http://" + host + "/"
	listener, err := net.Listen("tcp", host)
	if err != nil {
		log.Fatalf("Cannot use %s. Close the other application or choose --port. %v", url, err)
	}
	tokenBytes := make([]byte, 32)
	if _, err = rand.Read(tokenBytes); err != nil {
		log.Fatal(err)
	}
	server := &http.Server{ReadHeaderTimeout: 5 * time.Second, IdleTimeout: 60 * time.Second}
	shutdownDone := make(chan struct{})
	var stopOnce sync.Once
	stop := func() {
		stopOnce.Do(func() {
			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer cancel()
			server.Shutdown(ctx)
			close(shutdownDone)
		})
	}
	server.Handler = handler(site, host, hex.EncodeToString(tokenBytes), stop)
	interrupted := make(chan os.Signal, 1)
	signal.Notify(interrupted, os.Interrupt)
	go func() { <-interrupted; stop() }()
	fmt.Printf("SimpleOpenCV %s\n%s\nKeep this launcher running. Use Quit desktop app in the footer, or Ctrl+C, to stop.\n", version, url)
	if !*noBrowser {
		if err = openBrowser(url); err != nil {
			fmt.Println("Open the URL above in your browser:", err)
		}
	}
	if err = server.Serve(listener); err != nil && err != http.ErrServerClosed {
		log.Fatal(err)
	}
	<-shutdownDone
}
