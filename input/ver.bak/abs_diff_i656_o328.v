module abs_diff_i656_o328(a,b,r);
input [327:0] a,b;
output [327:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
