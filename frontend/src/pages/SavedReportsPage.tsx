import React, { useState, useEffect } from 'react';
import { BookmarkCheck, Trash2, Download, Search } from 'lucide-react';
import { api } from '../services/api';
import { SavedReport } from '../types';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { Input } from '../components/ui/Input';
import { Modal } from '../components/ui/Modal';
import { Skeleton } from '../components/ui/Skeleton';
import { useToast } from '../context/ToastContext';

export const SavedReportsPage: React.FC = () => {
  const { success, error } = useToast();

  const [reports, setReports] = useState<SavedReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewingReport, setViewingReport] = useState<SavedReport | null>(null);

  useEffect(() => {
    async function loadReports() {
      try {
        const data = await api.reports.list(selectedType === 'all' ? undefined : selectedType);
        setReports(data);
      } catch (err) {
        console.error('Failed to load reports', err);
      } finally {
        setLoading(false);
      }
    }
    loadReports();
  }, [selectedType]);

  const handleDelete = async (id: string) => {
    try {
      await api.reports.delete(id);
      setReports((prev) => prev.filter((r) => r.id !== id));
      success('Report Removed', 'Report has been deleted from your archive.');
    } catch (err: any) {
      error('Delete Failed', err.message || 'Could not delete report.');
    }
  };

  const handleDownload = (report: SavedReport) => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `talentverse_${report.report_type}_${report.id.substring(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    success('Exported', 'Saved report JSON dossier downloaded.');
  };

  const filteredReports = reports.filter((r) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      r.title.toLowerCase().includes(query) ||
      (r.summary && r.summary.toLowerCase().includes(query)) ||
      r.tags.some((t) => t.toLowerCase().includes(query))
    );
  });

  return (
    <div className="space-y-8 pb-16">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
          Saved Intelligence Reports
        </h1>
        <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
          Review, export, and manage your complete historical dossier of resume analyses, roadmap revisions, job fit benchmarks, and mock interviews.
        </p>
      </div>

      {/* Filters and Search Bar */}
      <Card>
        <CardContent className="p-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
            {['all', 'resume', 'roadmap', 'job_match', 'project', 'interview'].map((type) => (
              <button
                key={type}
                onClick={() => setSelectedType(type)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold uppercase tracking-wider transition-all whitespace-nowrap ${
                  selectedType === type
                    ? 'bg-brand-500 text-white shadow-xs'
                    : 'text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800'
                }`}
              >
                {type.replace('_', ' ')}
              </button>
            ))}
          </div>

          <div className="w-full sm:w-64">
            <Input
              placeholder="Search reports or tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              leftIcon={<Search className="w-4 h-4" />}
            />
          </div>
        </CardContent>
      </Card>

      {/* Reports Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Skeleton className="h-56 rounded-2xl" />
          <Skeleton className="h-56 rounded-2xl" />
          <Skeleton className="h-56 rounded-2xl" />
        </div>
      ) : filteredReports.length === 0 ? (
        <Card className="p-12 text-center text-slate-500">
          <BookmarkCheck className="w-12 h-12 mx-auto text-slate-300 dark:text-slate-700 mb-3" />
          <p className="text-base font-semibold text-slate-700 dark:text-slate-300">
            No saved reports found
          </p>
          <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
            Run a resume analysis, career roadmap, or interview session to auto-save reports to your dossier.
          </p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredReports.map((report) => (
            <Card key={report.id} className="flex flex-col justify-between hover:shadow-subtle transition-all">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <Badge
                    variant={
                      report.report_type === 'resume'
                        ? 'brand'
                        : report.report_type === 'roadmap'
                        ? 'indigo'
                        : report.report_type === 'job_match'
                        ? 'success'
                        : report.report_type === 'interview'
                        ? 'warning'
                        : 'cyan'
                    }
                    size="sm"
                  >
                    {report.report_type.replace('_', ' ').toUpperCase()}
                  </Badge>
                  {report.score !== undefined && report.score !== null && (
                    <span className="text-xs font-mono font-bold text-slate-700 dark:text-slate-300">
                      Score: {report.score}%
                    </span>
                  )}
                </div>
                <CardTitle className="text-base leading-snug">{report.title}</CardTitle>
                <CardDescription className="text-xs line-clamp-2 mt-1">
                  {report.summary}
                </CardDescription>
              </CardHeader>

              <CardContent className="pt-0 space-y-3">
                {/* Tags */}
                <div className="flex flex-wrap gap-1.5">
                  {report.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      className="text-[10px] px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-medium"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <div className="text-[11px] text-slate-400">
                  {report.created_at ? new Date(report.created_at).toLocaleDateString() : 'Recent'}
                </div>
              </CardContent>

              <div className="p-4 pt-0 border-t border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
                <Button
                  onClick={() => setViewingReport(report)}
                  variant="ghost"
                  size="sm"
                >
                  View Details
                </Button>

                <div className="flex items-center gap-1">
                  <button
                    onClick={() => handleDownload(report)}
                    title="Download JSON"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  >
                    <Download className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(report.id)}
                    title="Delete"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-rose-500 hover:bg-rose-50 dark:hover:bg-rose-950/30 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Report Modal */}
      {viewingReport && (
        <Modal
          isOpen={Boolean(viewingReport)}
          onClose={() => setViewingReport(null)}
          title={viewingReport.title}
          description={`Report ID: ${viewingReport.id} • ${viewingReport.report_type.toUpperCase()}`}
          maxWidth="2xl"
          footer={
            <div className="flex items-center justify-between w-full">
              <Button
                onClick={() => handleDownload(viewingReport)}
                variant="outline"
                size="sm"
                leftIcon={<Download className="w-4 h-4" />}
              >
                Download JSON
              </Button>
              <Button onClick={() => setViewingReport(null)} variant="secondary" size="sm">
                Close
              </Button>
            </div>
          }
        >
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-50 dark:bg-navy-950 text-xs sm:text-sm text-slate-700 dark:text-slate-300">
              <span className="font-semibold text-slate-900 dark:text-white">Summary: </span>
              {viewingReport.summary}
            </div>

            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-slate-400 block mb-2">
                Structured Report Data:
              </span>
              <pre className="p-4 rounded-xl bg-slate-900 text-slate-100 text-xs font-mono overflow-x-auto max-h-80">
                {JSON.stringify(viewingReport.data, null, 2)}
              </pre>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
