module abs_diff_i964_o482(a,b,r);
input [481:0] a,b;
output [481:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
