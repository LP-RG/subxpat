module abs_diff_i96_o48(a,b,r);
input [47:0] a,b;
output [47:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
