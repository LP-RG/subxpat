module abs_diff_i772_o386(a,b,r);
input [385:0] a,b;
output [385:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
