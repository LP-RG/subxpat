module abs_diff_i452_o226(a,b,r);
input [225:0] a,b;
output [225:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
