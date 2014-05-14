# You can add custom puppet manifests for your app here.
class custom {
  exec { 'append-lc_ctype-to-environments':
    command => 'echo "LC_CTYPE=en_US.UTF-8" >> /etc/environment',
    unless  => 'grep LC_CTYPE="en_US.UTF-8" /etc/environment',
  }
}
