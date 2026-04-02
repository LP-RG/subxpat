module abs_diff_i492_o246(a,b,r);
input [245:0] a,b;
output [245:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
