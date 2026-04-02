module abs_diff_i708_o354(a,b,r);
input [353:0] a,b;
output [353:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
