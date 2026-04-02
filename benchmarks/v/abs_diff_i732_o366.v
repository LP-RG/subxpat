module abs_diff_i732_o366(a,b,r);
input [365:0] a,b;
output [365:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
