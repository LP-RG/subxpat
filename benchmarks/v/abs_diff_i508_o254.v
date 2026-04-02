module abs_diff_i508_o254(a,b,r);
input [253:0] a,b;
output [253:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
