package com.ufpso.horarios

import android.annotation.SuppressLint
import android.app.Activity
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.*
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout
import androidx.webkit.WebViewAssetLoader

class MainActivity : AppCompatActivity() {

    private lateinit var webView: WebView
    private lateinit var swipeRefresh: SwipeRefreshLayout
    private var fileChooserCallback: ValueCallback<Array<Uri>>? = null

    private val liveServerUrl = "http://10.81.48.45:8000/"
    private val localFallbackUrl = "https://appassets.androidplatform.net/assets/web/index.html"
    private var isUsingFallback = false

    private val filePickerLauncher = registerForActivityResult(
        ActivityResultContracts.StartActivityForResult()
    ) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val intent = result.data
            val results: Array<Uri>? = when {
                intent?.clipData != null -> {
                    val count = intent.clipData!!.itemCount
                    Array(count) { i -> intent.clipData!!.getItemAt(i).uri }
                }
                intent?.data != null -> arrayOf(intent.data!!)
                else -> null
            }
            fileChooserCallback?.onReceiveValue(results)
        } else {
            fileChooserCallback?.onReceiveValue(null)
        }
        fileChooserCallback = null
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        swipeRefresh = SwipeRefreshLayout(this).apply {
            setColorSchemeColors(android.graphics.Color.parseColor("#DC2626"))
        }

        // Configurar WebViewAssetLoader para servir assets locales bajo origen seguro HTTPS
        val assetLoader = WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", WebViewAssetLoader.AssetsPathHandler(this))
            .build()

        webView = WebView(this).apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.allowFileAccess = true
            settings.allowContentAccess = true
            settings.loadWithOverviewMode = true
            settings.useWideViewPort = true
            settings.databaseEnabled = true
            settings.cacheMode = WebSettings.LOAD_DEFAULT
            settings.mixedContentMode = WebSettings.MIXED_CONTENT_ALWAYS_ALLOW

            webViewClient = object : WebViewClient() {
                override fun shouldInterceptRequest(
                    view: WebView,
                    request: WebResourceRequest
                ): WebResourceResponse? {
                    return assetLoader.shouldInterceptRequest(request.url)
                }

                override fun onPageFinished(view: WebView?, url: String?) {
                    super.onPageFinished(view, url)
                    swipeRefresh.isRefreshing = false
                }

                override fun onReceivedError(
                    view: WebView?,
                    request: WebResourceRequest?,
                    error: WebResourceError?
                ) {
                    super.onReceivedError(view, request, error)
                    swipeRefresh.isRefreshing = false
                    // Si el servidor en vivo no responde (ej. sin red local), cargar fallback local empaquetado
                    val failingUrl = request?.url?.toString() ?: ""
                    if (!isUsingFallback && failingUrl.startsWith(liveServerUrl)) {
                        isUsingFallback = true
                        webView.loadUrl(localFallbackUrl)
                    }
                }
            }

            webChromeClient = object : WebChromeClient() {
                override fun onShowFileChooser(
                    webView: WebView?,
                    filePathCallback: ValueCallback<Array<Uri>>?,
                    fileChooserParams: FileChooserParams?
                ): Boolean {
                    fileChooserCallback?.onReceiveValue(null)
                    fileChooserCallback = filePathCallback

                    val intent = Intent(Intent.ACTION_GET_CONTENT).apply {
                        addCategory(Intent.CATEGORY_OPENABLE)
                        type = "application/pdf"
                    }
                    filePickerLauncher.launch(Intent.createChooser(intent, "Seleccionar Horario SIA (PDF)"))
                    return true
                }
            }
        }

        swipeRefresh.addView(webView)
        swipeRefresh.setOnRefreshListener {
            isUsingFallback = false
            webView.loadUrl(liveServerUrl)
        }

        setContentView(swipeRefresh)

        // Cargar preferentemente desde el servidor en vivo para que los cambios se reflejen de inmediato
        webView.loadUrl(liveServerUrl)
    }

    @Deprecated("Deprecated in Java")
    override fun onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack()
        } else {
            super.onBackPressed()
        }
    }
}
