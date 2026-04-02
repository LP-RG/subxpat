module abs_diff_i580_o290(a,b,r);
input [289:0] a,b;
output [289:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
